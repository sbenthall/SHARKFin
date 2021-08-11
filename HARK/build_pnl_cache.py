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

    parser.add_argument("--sl_max", help="seed max", type=int, default=20)
    parser.add_argument("--sl_min", help="seed min", type=int, default=0)

    parser.add_argument('--bl_max',
                        help="buy limit max",
                        const=1,
                        type=int, default=20)
    parser.add_argument('--sl_max',
                        help="sell limit max",
                        const=1,
                        type=int,
                        default=20)

    parser.add_argument('--bl_min',
                        help="buy limit min",
                        const=1,
                        type=int,
                        default=0)
    parser.add_argument('--sl_min',
                        help="sell limit min",
                        const=1,
                        type=int,
                        default=0)

    args = parser.parse_args()

    pool = multiprocessing.Pool()
    records = pool.imap(
        do_market, case_generator(
            seed_max = args.sl_max,
            seed_min = args.sl_min,
            bl_max = args.bl_max,
            bl_min = args.bl_min,
            sl_max = args.sl_max,
            sl_min = args.sl_min
        ))
    pool.close()

    print("Cache building run complete")
    total_runs = len([r for r in records if r[1]])
    print(f"Ran {total_runs}")

if __name__ == "__main__":
    main()
