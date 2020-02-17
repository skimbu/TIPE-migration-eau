import math
from typing import Dict, List, Tuple

import pandas as pd


class Country(object):
    def __init__(self, name, populations: Dict[str, List[int]], water: List[float],
                 water_change_rate: float, required_water_per_person: float,
                 distances: Dict[str, float],
                 population_growth_rate: float, country_code: str, coordinates: Tuple[float], area: int, region: str):
        self.distances = distances
        self.iso_alpha = country_code
        self.name = name
        self.populations = populations
        self.water = water
        self.water_change_rate = water_change_rate
        self.required_water_per_person = required_water_per_person
        self.population_growth_rate = population_growth_rate
        self.coordinates = coordinates
        self.area = area
        self.region = region

    def calculate_exedant_water(self, time: int) -> float:
        population = sum([pop[time] for pop in self.populations.values()])
        required_water = population * self.required_water_per_person
        return self.water[time] - required_water

    def calculate_year_change(self, time, countries: Dict[str, 'Country']):
        new_water_amount = self.water[time] * self.water_change_rate
        total_population = sum([pop[time] for pop in self.populations.values()]) * self.population_growth_rate

        self.water.append(new_water_amount)

        max_population = new_water_amount / self.required_water_per_person
        if max_population >= total_population:
            # if the new population still has enough to drink, no-one will migrate
            migration_change_ratio = 1.0
        else:
            migration_change_ratio = max_population / total_population

        for population_name, population in self.populations.items():
            new_population = population[time] * self.population_growth_rate * migration_change_ratio

            new_population = int(new_population)

            migrating_count = population[time] - new_population
            if len(population) > time + 1:
                # some people already migrated here this year we need to include them too
                population[time+1] = population[time + 1] + new_population
            else:
                population.append(int(new_population))
            if migrating_count > 0:
                self.migrate(time, population_name, migrating_count, countries)

    def migrate(self, time: int, population_name: str, migrating_count: int,
                countries: Dict[str, 'Country']):

        weights = dict()

        for candidate in countries.values():

            if candidate == self:
                continue

            available_water = candidate.calculate_exedant_water(time)
            if available_water < 0:
                continue

            possible_migration = available_water / candidate.required_water_per_person

            # calculate weight based upon available headcount divided by distance, can evolve this
            weight = possible_migration / self.distances.get(candidate.name)

            weights[candidate.name] = weight

        if not weights:
            # TODO no-one can migrate - nowhere has enough water
            return

        # now work out migration ratios based on distance
        total_weight = sum([weight for weight in weights.values()])
        for name, weight in weights.items():
            country = countries.get(name)
            current_population_timeseries = country.populations.get(population_name)  # returns list of population originating from the country
            population_change = migrating_count * weight / total_weight
            if len(current_population_timeseries) > time + 1:
                current_population_timeseries[time+1] = current_population_timeseries[time+1] + population_change
            else:
                current_population_timeseries.append(population_change)

    def __repr__(self) -> str:
        return f'[ name={self.name}, populations={self.populations} ]'

    def to_panda(self, countries: Dict[str, 'Country']):
        # convert this region into a panda in tabular format suitable for passing into plotly

        # we aggregate migrated populations by region
        data = []
        for year in range(len(next(iter(self.populations.values())))):
            # emit rows year by year
            # plotly doesn't support pie charts, so generate overlayed circular markers for
            # people from different origins.
            # In order to display nicely, draw the largest circle first, and overlay with
            # successive smaller circles.

            region_populations = dict()
            year_data = []
            for origin_country_name in self.populations.keys():
                pop = self.populations.get(origin_country_name)[year]
                if pop == 0:
                    continue
                origin_country = countries.get(origin_country_name)
                if not origin_country:
                    continue
                region = origin_country.region

                prev_value = region_populations.get(region)
                region_populations[region] = prev_value + pop if prev_value else pop

            # Calculate the size of the largest circle (total population)
            pop_total = sum([value for value in region_populations.values()])
            remaining_pop = pop_total
            for origin, pop in region_populations.items():
                # don't display small population percentages
                if pop < pop_total * 0.02:
                    continue
                pop_percent = f"{int(pop / pop_total * 100)}%"
                # the rings on the outer circles appear small as the area is spread all around the edge of the circle
                # so make the circle size growth non-linear so outer rings are a bit larger
                size = remaining_pop**1.3
                # append a data row in the correct format (see DataFrame below)
                water_per_person = 0 if pop_total == 0 else int(self.water[year] / pop_total)
                year_data.append([year, self.name, self.iso_alpha, origin, int(pop_total)/1000, int(pop)/1000, pop_percent, size, water_per_person, self.required_water_per_person])
                # adjust the size of the next (smaller) overlayed circle by subtracting this population
                remaining_pop = remaining_pop - pop
            # sort the data by the size of circles so we draw inner circles on top of outer ones
            year_data.sort(key=lambda x: x[5])
            data.extend(year_data)

        # Create the pandas DataFrame with one row per point to plot
        df = pd.DataFrame(data, columns=['year', 'name', 'country_code', 'origin', 'population', 'pop_from_region', 'percentage', 'size', 'water_per_person', 'required_water_per_person'])
        return df
