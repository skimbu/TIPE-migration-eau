import json
import math
from collections import OrderedDict

from geopy.distance import geodesic

from country import Country
import pandas as pd
import plotly.express as px

# read raw country data
with open('countries.json') as json_file:
    country_data = json.load(json_file)

# read country population data
population_data = pd.read_csv("population.csv")

# read country water data
water_data = pd.read_csv("water_per_capita.csv")

# populate our regions from country data
countries = dict()
regions = set()


def calculate_fresh_water_change_rate(coords) -> float:
    # we model water change rate inversely proportional to the distance from the equator

    lat = coords[0]
    # calculate a linear number between 0 and 0.2 for latitudes 60 degrees north or south and a little more further away
    delta = abs(lat) / 60 * 0.2
    # calculate a value of 0.9 for countries on the equator evolving up to 1.1 for countries at 60 degrees n/s
    rate = 0.9 + delta
    assert 0.5 < rate < 1.5
    return rate


def init_regions():
    for country in country_data:
        region = country.get('region')
        if region:
            regions.add(region)


def lookup_csv_data(data: pd, country_code: str, year: int):
    value = None
    # look up most recent value if one is available
    while not value and year > 2000:
        cell = data.loc[population_data['Country Code'] == country_code][str(year)]
        if cell.values.size >= 1:
            value = cell.values[0]
            if math.isnan(value):
                value = None
        year = year - 1
    return int(value) if value else None


def filter_country(name):
    return (len(countries) > 100 and name != 'France') or name == 'China' or name == 'India'


def init_countries():
    print('Initializing country data')
    for country in country_data:

        name = country.get('name').get('common')
        if filter_country(name):
            continue

        region = country.get('region')
        # skip if missing region
        if not region:
            continue

        # now populate the Country
        country_code = country.get("cca3")
        coordinates = country.get("latlng")
        area = country.get("area")

        population = lookup_csv_data(population_data, country_code, 2018)
        if not population:
            continue

        required_water_per_person = lookup_csv_data(water_data, country_code, 2014)
        if not required_water_per_person:
            continue
        water_change_rate = calculate_fresh_water_change_rate(coordinates)

        initial_water = required_water_per_person * population * water_change_rate
        pop_growth_rate = 1.01  # todo

        populations = OrderedDict({name: [population]})
        distances = dict()
        # init migrated populations and distances from each other country
        for other_country in country_data:
            other_name = other_country.get('name').get('common')
            if other_name == name:
                continue
            populations[other_name] = [0]
            # calculate distance, or use existing calculation if already done (takes a few seconds for all countries)
            if countries.get(other_name):
                distances[other_name] = countries.get(other_name).distances.get(name)
            else:
                distances[other_name] = geodesic(coordinates, other_country.get("latlng")).kilometers

        countries[name] = Country(name=name,
                                  populations=populations,
                                  water=[initial_water],
                                  water_change_rate=water_change_rate,
                                  coordinates=coordinates,
                                  area=area,
                                  region=region,
                                  country_code=country_code,
                                  required_water_per_person=required_water_per_person,
                                  distances=distances,
                                  population_growth_rate=pop_growth_rate,
                                  )


def simulate():
    # simulate migrations through time
    for time in range(10):
        print(f"calculating year {time}")
        for country in countries.values():
            country.calculate_year_change(time, countries)


def view():
    print("Preparing data for rendering")
    # now integrate with plotting library by converting simulation to a 2d panda suitable for plotly scatter_geo plot
    data = []
    for country in countries.values():
        data.append(country.to_panda(countries))

    # concatenate the individual pandas into a single dataset
    data = pd.concat(data)

    # now use plotly express to draw an animated scatter_geo with this data
    print("Displaying data in browser")
    fig = px.scatter_geo(data, locations="country_code", color="origin", hover_name="name", hover_data=['population', 'pop_from_region', 'percentage', 'water_per_person', 'required_water_per_person'], size="size",
                         animation_frame="year", projection="natural earth", opacity=0.8, size_max=20)
    fig.show()


init_regions()
init_countries()
simulate()
view()


