from Statistics import *


def main():
    from multiprocessing import Pool
    from random import seed, random
    from tqdm import tqdm

    from Banner import Rarity

    # Number of Wishers
    N = 100

    # Seed RNG
    seed('Another Random Seed of my Choice.')

    # Create List of Random Seeds.
    seeds = [(random(), 1000 * 91) for x in range(N)]

    # Computations
    compute_chain = ConsolidatedProbability(Rarity.ThreeStar, ConsolidatedProbability(Rarity.FourStar, ConsolidatedProbability(Rarity.FiveStar, DistributionOfTimeUntilFiveStar(MedianTimeUntilFiveStar(AverageTimeUntilFiveStar(AverageTimeUntilFeaturedFiveStar()))))))

    # Run Simulation
    with Pool(5) as workers:
        for stars in tqdm(workers.imap_unordered(wish_simulator, seeds, chunksize=5), total=len(seeds), leave=True):
            compute_chain.send(stars)

    # Print out result
    compute_chain.print()
    compute_chain.dump()


def wish_simulator(data):
    from Banner import GenericCharacterBanner

    seed, n = data
    banner = GenericCharacterBanner(seed)

    stars = list()
    for i in range(n):
        stars.append(banner.wish())

    return stars


if __name__ == '__main__':
    main()
