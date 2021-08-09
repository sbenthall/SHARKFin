import hark_portfolio_agents as hpa

AZURE = True

fill = False

def case_generator():
    seed_limit = 60
    limit_total = 600

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

market = hpa.MarketPNL()
                
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
                
import multiprocessing

pool = multiprocessing.Pool()
records = pool.imap(do_market, case_generator())
pool.close()

print("Cache building run complete")
total_runs = len([r for r in records if r[1]])
print(f"Ran {total_runs}")
