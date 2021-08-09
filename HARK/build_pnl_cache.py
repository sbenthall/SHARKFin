import argparse
import hark_portfolio_agents as hpa
import multiprocessing

AZURE = True

market = hpa.MarketPNL()

def case_generator(
    seed_limit = 5,
    limit_total = 10,
    fill = False
    ):
    for t in range(limit_total):
        for seed in range(seed_limit):
            r = range(t + 1) if fill else [t, 0]

            for buy_limit in r:
                yield (
                    seed,
                    (
                        buy_limit,
                        t - buy_limit
                    ))
                
def do_market(args):
    print(args)
    seed = args[0]
    buy_sell = args[1]

    try:
        market.run_market(
            seed = seed,
            buy_sell = buy_sell
        )
        return (args , True)
    except Exception as e:
        return (args , False)
                
def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("sl", help="seed limit",
                    type=int)
    parser.add_argument("lt", help="total buy and sell limit total",
                    type=int)
    parser.add_argument("--fill", help="fill in every value not just (x,0) and (0,x)",
                    action="store_true")

    args = parser.parse_args()

    pool = multiprocessing.Pool()
    records = pool.imap(
        do_market, case_generator(
            seed_limit = args.sl,
            limit_total = args.lt,
            fill = args.fill
        ))
    pool.close()

    print("Cache building run complete")
    total_runs = len([r for r in records if r[1]])
    print(f"Ran {total_runs}")

if __name__ == "__main__":
    main()
