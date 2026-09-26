"""
Phase 2: live monitoring mechanism.

Polls Monad mainnet directly for a stream's current onchain state, recomputes
the Phase 1 scoring formula, and reports whether the result changed since the
last poll. No LLM involvement. Every poll logs the block number and
timestamp it read, per the reproducibility rule.

This is deliberately forward-looking only, not retrospective: querying
rpc.monad.xyz for a block older than its sliding retention window returns
JSON-RPC error -32602 ("Block requested not found ... querying historical
state that is not available"), confirmed live during Phase 2 verification
(see BUILDLOG.md). There is no stable archive to reconstruct past state
from on this endpoint, so the monitoring model here is poll-forward-in-time,
not scan-backward-in-history. That constraint is actually consistent with
the thesis: this is built to catch drift going forward in near-real-time,
not to audit the past.
"""

import json
import time
import urllib.error
import urllib.request

from model import Stream, ScoringInput, score

RPC_URL = "https://rpc.monad.xyz"
CONTRACT = "0x82723c1ffec9d43de5fa80b25da8df99afd470ba"  # SablierLockup, Monad mainnet

SEL = {
    "owner": "0x6352211e",
    "sender": "0xb971302a",
    "deposited": "0xa80fc071",
    "withdrawn": "0xd511609f",
    "start": "0xbc2be1be",
    "end": "0x9067b677",
    "cancelable": "0x4857501f",
    "canceled": "0xf590c176",
}


def _rpc(method, params, retries=8):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(RPC_URL, data=body, headers={"Content-Type": "application/json"})
    for i in range(retries):
        try:
            return json.loads(urllib.request.urlopen(req).read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(1.2 * (i + 1))
                continue
            raise RuntimeError(f"RPC HTTP {e.code}: {e.read().decode()}")
    raise RuntimeError("RPC rate-limited past retry budget")


def _call(selector, stream_id, block="latest"):
    arg = hex(stream_id)[2:].rjust(64, "0")
    r = _rpc("eth_call", [{"to": CONTRACT, "data": selector + arg}, block])
    if "error" in r:
        raise RuntimeError(r["error"])
    return r["result"]


def _addr(h):
    return "0x" + h[-40:]


def _bool(h):
    return int(h, 16) == 1


def read_stream(stream_id: int, block: str = "latest") -> tuple[Stream, int, int]:
    """Read one stream's live state, plus the block number and timestamp it
    was read at (both taken from the same eth_call block tag to keep the
    reading atomic and reproducible)."""
    if block == "latest":
        block_number = int(_rpc("eth_blockNumber", [])["result"], 16)
        block_tag = hex(block_number)
    else:
        block_number = block
        block_tag = hex(block)

    blk = _rpc("eth_getBlockByNumber", [block_tag, False])["result"]
    timestamp = int(blk["timestamp"], 16)

    stream = Stream(
        stream_id=stream_id,
        sender=_addr(_call(SEL["sender"], stream_id, block_tag)),
        deposit_amount=int(_call(SEL["deposited"], stream_id, block_tag), 16),
        withdrawn_amount=int(_call(SEL["withdrawn"], stream_id, block_tag), 16),
        start_time=int(_call(SEL["start"], stream_id, block_tag), 16),
        end_time=int(_call(SEL["end"], stream_id, block_tag), 16),
        cancelable=_bool(_call(SEL["cancelable"], stream_id, block_tag)),
        canceled=_bool(_call(SEL["canceled"], stream_id, block_tag)),
    )
    return stream, block_number, timestamp


def poll(stream_id: int, requested_credit_line: float, loan_term_seconds: int):
    stream, block_number, timestamp = read_stream(stream_id)
    inputs = ScoringInput(
        streams=[stream],
        requested_credit_line=requested_credit_line,
        loan_term_seconds=loan_term_seconds,
        as_of_time=timestamp,
        block_number=block_number,
    )
    return score(inputs), stream


if __name__ == "__main__":
    import sys

    stream_id = int(sys.argv[1]) if len(sys.argv) > 1 else 23
    requested = float(sys.argv[2]) if len(sys.argv) > 2 else 1_000_000e18
    loan_term = int(sys.argv[3]) if len(sys.argv) > 3 else 30 * 24 * 60 * 60

    result, stream = poll(stream_id, requested, loan_term)
    print(f"block={result.block_number} t={result.as_of_time} "
          f"withdrawn={stream.withdrawn_amount/1e18:,.2f} canceled={stream.canceled} "
          f"coverage_ratio={result.coverage_ratio:.6f} tier={result.tier.value} "
          f"approved_line={result.approved_line/1e18:,.2f}")
