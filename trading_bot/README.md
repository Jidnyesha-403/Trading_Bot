# Simplified Trading Bot — Binance Futures Testnet (USDT-M)

A small, structured Python CLI application for placing MARKET, LIMIT, and
STOP orders on the Binance Futures Testnet, with input validation,
structured logging, and clean error handling.

## Project structure

```
trading_bot/
  bot/
    __init__.py
    config.py           # env/config loading, credential checks
    client.py            # low-level signed REST client (requests)
    orders.py             # order payload building + placement logic
    validators.py          # CLI input validation
    logging_config.py       # rotating file + console logging setup
  tests/
    test_validators.py       # unit tests for validation logic
  cli.py                       # CLI entry point (argparse)
  requirements.txt
  .env.example
  README.md
```

**Layering:** `cli.py` only parses arguments and prints results. It never
talks to Binance directly — that's `client.py`'s job. `orders.py` sits in
between, turning validated input into the right Binance payload per order
type. This means the client or CLI can each be replaced/tested
independently (e.g. swapping `requests` for `httpx`, or adding a web UI
that reuses `OrderService` directly).

## Setup

### 1. Get Binance Futures Demo Trading credentials

Binance retired the old GitHub-login futures testnet
(`testnet.binancefuture.com`) in favor of **Demo Trading**, a sandbox
built into a regular Binance.com account:

1. Log in to https://www.binance.com with your normal account.
2. Open **Binance Demo Trading** (a separate sandbox environment with
   fake funds, distinct from your real balance).
3. Inside Demo Trading, go to its **API Key Management** page and
   generate a demo API key/secret pair.
4. Demo accounts come pre-loaded with fake USDT so orders can fill
   immediately.

The REST base URL for this environment is `https://demo-fapi.binance.com`
(already set as the default in `bot/config.py`).

### 2. Install dependencies

```bash
git clone <your-repo-url>
cd trading_bot
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```

Credentials are loaded via `python-dotenv` and never hardcoded or logged
in full (the client redacts signatures in logs).

## Running the bot

### Market order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Limit order

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000
```

### Stop-Market order (bonus order type)

```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.01 --stop-price 58000
```

### Stop-Limit order

```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP --quantity 0.01 --price 58500 --stop-price 58000
```

### Sample output

```
--- Order Request ---
  symbol: BTCUSDT
  side: BUY
  type: MARKET
  quantity: 0.01
--- Order Response ---
  orderId     : 3487123456
  status      : FILLED
  executedQty : 0.01
  avgPrice    : 60123.40
RESULT: SUCCESS - order placed on Binance Futures Testnet.
```

On failure (invalid symbol, insufficient testnet balance, network issue,
etc.), the CLI prints a `RESULT: FAILURE - <reason>` line and exits with a
non-zero status code, and the full error is captured in the log file.

## Logging

All requests, responses, and errors are logged to `logs/trading_bot.log`
(rotating at 2MB, 5 backups kept). Console output only shows INFO-level
summaries so day-to-day use isn't noisy, while the log file keeps DEBUG
detail (full request params with the signature redacted, full response
bodies, stack traces on unexpected errors) for later review or
troubleshooting. Sample log excerpts from a MARKET and a LIMIT order run
are included in `logs/trading_bot.log` (or see `sample_logs/` if you
regenerate and want to keep a copy of a specific run).

## Running the tests

```bash
python -m unittest discover -s tests -v
```

These are pure unit tests against the validation layer — no network
calls, so they run instantly and don't require API keys.

## Assumptions & design decisions

- **REST calls over python-binance**: implemented directly with
  `requests` + HMAC-SHA256 signing rather than the `python-binance`
  library, to keep the dependency footprint small and make the exact
  request/response cycle fully transparent for logging and review.
- **Time-in-force**: LIMIT and STOP orders default to `GTC`
  (Good-Til-Cancelled), the standard default for orders not meant to
  expire immediately. This isn't currently exposed as a CLI flag; it
  would be a natural next addition.
- **Order types implemented**: MARKET, LIMIT, plus STOP and STOP_MARKET
  as the bonus third order type (a stop-limit and a stop-market variant),
  since these reuse the same signed `/fapi/v1/order` endpoint with a few
  extra parameters.
- **No quantity/price step-size auto-rounding**: the bot validates that
  quantity/price are positive numbers, but does not currently round them
  to each symbol's `LOT_SIZE`/`PRICE_FILTER` tick size (Binance will
  reject invalid precision with a clear API error, which is logged and
  surfaced to the user). `client.get_symbol_filters()` is provided as a
  building block for adding this.
- **Single account, single environment**: credentials are read once from
  environment variables / `.env`; no multi-account or mainnet/testnet
  switching UI was built, since the task is scoped to the testnet only.
- **Demo/testnet only**: `BASE_URL` defaults to
  `https://demo-fapi.binance.com` (Binance's current Futures Demo Trading
  endpoint, which replaced the old `testnet.binancefuture.com`). Do not
  point this at the mainnet URL (`https://fapi.binance.com`) without a
  thorough review — this code was written and reviewed only with
  demo/testnet risk in mind.

## Bonus implemented

- **Third order type**: STOP and STOP_MARKET orders (stop-limit and
  stop-market), in addition to MARKET and LIMIT.
- **Input validation layer** (`bot/validators.py`) with clear,
  actionable error messages for every field (symbol format, side,
  order type, quantity, price/stop-price requirements per order type).
