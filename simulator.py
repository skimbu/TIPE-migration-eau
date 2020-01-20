from collections import OrderedDict

from region import Region
import pandas as pd
import plotly.express as px

regions = dict()

regions['europe'] = Region(name='europe', populations=OrderedDict({ 'europe' : [100000] }), neighbours={ 'africa' : 1.0 },
                           water=[1000000], water_change_rate=1.0, required_water_per_person=5,
                           country_code='FRA',
                           population_growth_rate=1.01)

regions['africa'] = Region(name='africa',
                           populations=OrderedDict({ 'africa' : [100000] }),
                           neighbours={ 'europe' : 1.0 },
                           water=[100000],
                           water_change_rate=0.9,
                           required_water_per_person=1,
                           country_code='CAF',
                           population_growth_rate=1.1)

# initialize each region's population from other regions to zero if not set above
for region in regions.values() :
    for region2 in regions.values() :
        if not region.populations.get(region2.name) :
            region.populations[region2.name] = [0]

# now simulate migrations through time
for time in range(10) :
    print(regions.values())
    for region in regions.values() :
        region.calculate_year_change(time, regions)

# now integrate with plotting library by converting simulation to a 2d panda suitable for plotly scatter_geo plot
data = []
for region in regions.values():
    data.append(region.to_panda())

# concatenate the individual pandas into a single dataset
data = pd.concat(data)

# now use plotly express to draw an animated scatter_geo with this data
fig = px.scatter_geo(data, locations="country_code", color="origin", hover_name="origin", hover_data=['population'], size="size",
               animation_frame="year", projection="natural earth")
fig.show()

