import math
from typing import Dict, List
import pandas as pd


class Region(object) :
    def __init__(self, name, populations: Dict[str, List[int]], neighbours: Dict[str, float], water: List,
                 water_change_rate: float, required_water_per_person: int, population_growth_rate: float, country_code: str) :
        self.iso_alpha = country_code
        self.name = name
        self.populations = populations
        self.neighbours = neighbours
        self.water = water
        self.water_change_rate = water_change_rate
        self.required_water_per_person = required_water_per_person
        self.population_growth_rate = population_growth_rate

    def calculate_year_change(self, time, regions: Dict[str, 'Region']):
        new_water_amount = self.water[time] * self.water_change_rate
        total_population = sum([pop[time] for pop in self.populations.values()])

        self.water.append(new_water_amount)

        max_population = self.required_water_per_person * new_water_amount
        if max_population >= total_population :
            # if the new population is not smaller, no-one will migrate
            migration_change_ratio = 1.0
        else :
            migration_change_ratio = max_population / total_population

        for population_name, population in self.populations.items():
            new_population = population[time] * migration_change_ratio

            migrating_count = population[time] - new_population
            if len(population) > time + 1 :
                # some people already migrated here this year we need to include them too
                population[time + 1] = population[time + 1] + new_population
            else :
                population.append(new_population)
            if migrating_count > 0 :
                self.migrate(time, self.name, population_name, migrating_count, regions)

    def migrate(self, time: int, region_name: str, population_name: str, migrating_count: int,
                regions: Dict[str, 'Region']) :

        destination_regions = dict()
        # first calculate the regions currently with enough water to which populations will migrate
        for name in self.neighbours.keys() :
            neighbour = regions[name] #initialise neighbour to its value in regions dictionary
            # calculate total population
            neighbour_population = sum([pop[time] for pop in neighbour.populations.values()])
            if neighbour.required_water_per_person * neighbour.water[time] > neighbour_population :
                destination_regions[name] = neighbour
        if not destination_regions :
            raise ValueError("improve algorithm!")
        # now work out migration ratios based on distance
        total_distances = sum([self.neighbours.get(name) for name in destination_regions.keys()]) #get returns value for key
        for name, region in destination_regions.items() :
            current_population_timeseries = region.populations.get(population_name) # returns list of population of region to migrate in region
            population_change = migrating_count * self.neighbours.get(name) / total_distances
            if len(current_population_timeseries) > time + 1 :
                current_population_timeseries[time + 1] = current_population_timeseries[time + 1] + population_change
            else :
                current_population_timeseries.append(population_change)

    def __repr__(self) -> str :
        return f'[ name={self.name}, populations={self.populations} ]'

    def to_panda(self):
        # convert this region into a panda in tabular format suitable for passing into plotly
        data = []
        for year in range(len(next(iter(self.populations.values())))):
            # emit rows year by year
            # plotly doesn't support pie charts, so generate overlayed circular markers for
            # people from different origins.
            # In order to display nicely, draw the largest circle first, and overlay with
            # successive smaller circles.

            # Calculate the size of the largest circle (total population)
            pop_total = sum([pop[year] for pop in self.populations.values()])
            for origin in self.populations.keys():
                # get the population for the year in question for the given population
                pop = self.populations.get(origin)[year]
                # append a row in the correct format (see DataFrame below)
                data.append([year, self.name, self.iso_alpha, origin, pop, pop_total])
                # adjust the size of the next (smaller) overlayed circle by subtracting this population
                pop_total = pop_total - pop

        # Create the pandas DataFrame with one row per point to plot
        df = pd.DataFrame(data, columns=['year', 'name', 'country_code', 'origin', 'population', 'size'])
        return df
