
class StatisticComputationNode:
    def __init__(self, child=None):
        self.child = child

    def send(self, data):
        self.compute(data)
        if self.child is None:
            return
        self.child.send(data)

    def compute(self, data):
        raise NotImplementedError()

    def _print(self):
        raise NotImplementedError()

    def _dump(self):
        pass

    def print(self):
        print("{} Statistics".format(type(self).__qualname__))
        self._print()
        if self.child is None:
            return
        print()
        print()
        self.child.print()

    def dump(self):
        self._dump()
        if self.child is None:
            return
        self.child.dump()


class AverageTimeUntilFeaturedFiveStar(StatisticComputationNode):
    def __init__(self, child=None):
        super().__init__(child)
        self.avg_wait_time = 0.0
        self.current_wait = 0
        self.current_sample_count = 0

    def compute(self, stars):
        from Banner import Rarity
        wait_time = 0
        for star in stars:
            if star.rarity == Rarity.FiveStar and star.name.find("Featured") != -1:
                self.current_wait = self.current_wait + wait_time
                self.current_sample_count = self.current_sample_count + 1
                wait_time = 0
            else:
                wait_time = wait_time + 1
        self.avg_wait_time = self.current_wait / self.current_sample_count if self.current_sample_count != 0 else 0.0

    def _print(self):
        print("Average = {}".format(self.avg_wait_time))


class AverageTimeUntilFiveStar(StatisticComputationNode):
    def __init__(self, child=None):
        super().__init__(child)
        self.avg_wait_time = 0.0
        self.current_wait = 0
        self.current_sample_count = 0

    def compute(self, stars):
        from Banner import Rarity
        wait_time = 0
        for star in stars:
            if star.rarity == Rarity.FiveStar:
                self.current_wait = self.current_wait + wait_time
                self.current_sample_count = self.current_sample_count + 1
                wait_time = 0
            else:
                wait_time = wait_time + 1
        self.avg_wait_time = self.current_wait / self.current_sample_count if self.current_sample_count != 0 else 0.0

    def _print(self):
        print("Average = {}".format(self.avg_wait_time))


class MedianTimeUntilFiveStar(StatisticComputationNode):
    def __init__(self, child=None):
        super().__init__(child)
        self.current_waits = list()

    def compute(self, stars):
        from Banner import Rarity
        wait_time = 0
        for star in stars:
            if star.rarity == Rarity.FiveStar:
                self.current_waits.append(wait_time)
                wait_time = 0
            else:
                wait_time = wait_time + 1

    def _print(self):
        self.current_waits.sort()
        print("Median = {}".format(self.current_waits[len(self.current_waits)//2]))


class ConsolidatedProbability(StatisticComputationNode):
    def __init__(self, rarity, child=None):
        super().__init__(child)
        self.count_num = 0
        self.count_den = 0
        self.rarity = rarity

    def compute(self, stars):
        self.count_den = self.count_den + len(stars)
        self.count_num = self.count_num + len(list(filter(lambda l: l.rarity == self.rarity, stars)))

    def _print(self):
        print("Consolidated Probability = {}".format(self.count_num / self.count_den))


class DistributionOfTimeUntilFiveStar(StatisticComputationNode):
    def __init__(self, child=None):
        super().__init__(child)
        self.current_waits = list()

    def compute(self, stars):
        from Banner import Rarity
        wait_time = 0
        for star in stars:
            if star.rarity == Rarity.FiveStar:
                self.current_waits.append(wait_time)
                wait_time = 0
            else:
                wait_time = wait_time + 1

    def _print(self):
        from numpy import histogram, array
        import numpy as np

        data = array(self.current_waits, dtype=np.uint16)
        bin_data = array([x for x in range(0, 91)], dtype=np.uint16)
        hist, b = histogram(data, bins=bin_data, density=True)

        for r in range(len(hist)):
            print("Probability to Get 5★ at Wish {} = {}".format(b[r] + 1, hist[r]))

    def _dump(self):
        import csv
        from numpy import histogram, array
        import numpy as np
        from tqdm import tqdm

        data = array(self.current_waits, dtype=np.uint16)
        bin_data = array([x for x in range(0, 91)], dtype=np.uint16)
        hist, b = histogram(data, bins=bin_data, density=True)

        with open('DATA-{}.csv'.format(type(self).__qualname__), 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['WISH', 'PROBABILITY'])
            for row in tqdm(range(len(hist)), desc='Dumping Statistics for {}'.format(type(self).__qualname__)):
                csvwriter.writerow(['{}'.format(b[row]), '{}'.format(hist[row])])
