import random
from enum import Enum
from math import sqrt
from itertools import product
import operator
import pprint
import copy

STD_NORM_05 = 1.96
STD_NORM_10 = 1.65

SIM_COUNT = 5
SIM_OVERSIZED_MULT = 0.3


class PlantType(Enum):
    BARLEY = 'BARLEY'
    WHEAT = 'WHEAT'
    OAT = 'OAT'
    COLZA = 'COLZA'


def create_sell_limitations():
    return {
        PlantType.BARLEY: {
            "max": 50,
            "produced": 0
        },
        PlantType.WHEAT: {
            "max": 60,
            "produced": 0
        },
        PlantType.OAT: {
            "max": 70,
            "produced": 0
        },
        PlantType.COLZA: {
            "max": 20,
            "produced": 0
        },
    }


def get_all_combinations_with_repetition(arr, rno):
    results = []
    for el in product(arr, repeat=rno):
        results.append(el)
    return results


def take_value_from_dist(dist: list):
    random_prob = random.random()
    prob_sum = 0
    for value, prob in dist:
        if random_prob >= prob_sum and random_prob < prob_sum + prob:
            return value
        else:
            prob_sum += prob


class Plant:
    def __init__(self, type: PlantType, price_per_ton_dist: list, harvest_per_ha_dist: list):
        self.type = type
        self.price_per_ton_dist = price_per_ton_dist
        self.harvest_per_ha_dist = harvest_per_ha_dist

    def take_price_per_ton(self):
        return take_value_from_dist(self.price_per_ton_dist)

    def take_harvest_per_ha(self):
        return take_value_from_dist(self.harvest_per_ha_dist)


class Field:
    def __init__(self, ha: int):
        self.ha = ha

    def get_income(self, plant_price_per_ton, plant_harvest_per_ha):
        return self.ha * plant_harvest_per_ha * plant_price_per_ton

    def __str__(self):
        return str(self.ha)


class Simulation:
    def __init__(self, iterations: int):
        self.iterations = iterations
        self.cases = []
        self.sum = 0.0
        self.average_income = 0.0
        self.max_income = 0.0
        self.min_income = float('inf')
        self.std_dev_income = 0.0
        self.left_conf_interval = 0.0
        self.right_conf_interval = 0.0

    def run_simulation(self, fields: Field, plants: Plant):
        for _ in range(self.iterations):
            sell_limitations = create_sell_limitations()

            fields_income = 0
            for i in range(len(fields)):
                income = self.calculate_field_with_plant_income(
                    sell_limitations, fields[i], plants[i])
                fields_income += income

            self.cases.append(fields_income)

            if fields_income > self.max_income:
                self.max_income = fields_income

            if fields_income < self.min_income:
                self.min_income = fields_income

            self.sum += fields_income

        self.average_income = self.sum / self.iterations

        self.calculate_std_dev_income()

    def calculate_field_with_plant_income(self, sell_limitations, field: Field, plant: Plant):
        plant_price_per_ton = plant.take_price_per_ton()
        plant_harvest_per_ha = plant.take_harvest_per_ha()

        harvest_size_tones = field.ha * plant_harvest_per_ha

        plant_sell_limitation = sell_limitations[plant.type]

        # OVERSIZE LIMITATIONS #
        field_income = 0
        if plant_sell_limitation['produced'] >= plant_sell_limitation['max']:
            field_income = field.get_income(
                plant_price_per_ton,
                plant_harvest_per_ha
            ) * SIM_OVERSIZED_MULT
        elif plant_sell_limitation['produced'] + harvest_size_tones > plant_sell_limitation['max']:
            plant_tones_missing_to_max = (plant_sell_limitation['max'] -
                                          plant_sell_limitation['produced'])
            plant_tones_over_max = (
                harvest_size_tones - plant_tones_missing_to_max)
            field_income = (plant_tones_missing_to_max * plant_price_per_ton +
                            plant_tones_over_max * plant_price_per_ton * SIM_OVERSIZED_MULT)
        else:
            field_income = field.get_income(
                plant_price_per_ton,
                plant_harvest_per_ha
            )
        sell_limitations[plant.type]['produced'] += harvest_size_tones
        #########################

        return field_income

    def calculate_std_dev_income(self):
        std_sum = 0

        for fields_income in self.cases:
            calc = (fields_income - self.average_income)
            std_sum += calc * calc

        self.std_dev_income = sqrt(std_sum / self.iterations)
        self.left_conf_interval = self.average_income - self.std_dev_income * STD_NORM_05
        self.right_conf_interval = self.average_income + self.std_dev_income * STD_NORM_05

    def __str__(self):
        return "Iterations {}\nAverage Income {}\nStd. Dev. Income {}\nMax Income {}\nMin Income {}".format(
            self.iterations,  self.average_income, self.std_dev_income, self.max_income, self.min_income)


def map_plants_ids_to_plants(plants_ids):
    return list(map(lambda id: plants[id], plants_ids))


def get_simulation_results(fields, plants, plants_variants, simulations_count):
    results = []
    print("Running simulations for {} fields, and {} plants, with total variants of {}".format(
        fields_count, plants_count, len(plants_variants)))
    for plant_variant in plants_variants:
        random.seed(1000)  # TODO: Napisać w docu LUL
        sim = Simulation(simulations_count)
        mapped_plants = map_plants_ids_to_plants(plant_variant)
        sim.run_simulation(fields, mapped_plants)
        plants_names = list(map(lambda x: x.type.name, mapped_plants))
        results.append((plants_names,
                        round(sim.average_income, 2),
                        round(sim.min_income, 2),
                        round(sim.max_income, 2),
                        round(sim.std_dev_income, 2),
                        round(sim.left_conf_interval, 2),
                        round(sim.right_conf_interval, 2)))
    results_sorted = sorted(results, key=lambda x: x[1], reverse=True)
    print("Simulations ended")
    return results_sorted


def save_results_to_csv(results):
    print("Saving results...")
    with open('zniwa.csv', 'w') as f:
        fields_input_string = "{}," * len(fields)
        fields_numbers_arr = list(range(1, len(fields) + 1))
        header_line = (fields_input_string +
                       "srednia,minimum,maksimum,odchylenie,dolny przedział ufności,górny przedział ufności\n").format(*fields_numbers_arr)
        lines = list(map(lambda x: (fields_input_string + "{},{},{},{},{},{}\n").format(
            *x[0], x[1], x[2], x[3], x[4], x[5], x[6]), results))
        lines.insert(0, header_line)
        f.writelines(lines)
    print("Results saved.")


barley = Plant(
    PlantType.BARLEY,
    (
        (540.63, 0.05),
        (564.74, 0.06),
        (600.5, 0.1),
        (620.6, 0.13),
        (654.7, 0.2),
        (680.6, 0.21),
        (690.02, 0.18),
        (720.74, 0.07),
    ),
    (
        (1.41, 0.02),
        (2.0, 0.06),
        (2.7, 0.1),
        (3.5, 0.13),
        (4.4, 0.23),
        (5.66, 0.36),
        (7.38, 0.08),
        (9.45, 0.02),
    )
)

wheat = Plant(
    PlantType.WHEAT,
    (
        (679.48, 0.05),
        (700.74, 0.06),
        (715.6, 0.10),
        (730.68, 0.13),
        (793.33, 0.20),
        (832.57, 0.21),
        (851.02, 0.18),
        (921.84, 0.07),
    ),
    (
        (2.00, 0.02),
        (2.67, 0.06),
        (3.11, 0.10),
        (3.56, 0.13),
        (4.22, 0.23),
        (4.72, 0.36),
        (5.87, 0.08),
        (6.00, 0.02),
    )
)

oat = Plant(
    PlantType.OAT,
    (
        (559.22, 0.05),
        (562.87, 0.06),
        (566.47, 0.10),
        (569.75, 0.13),
        (577.99, 0.20),
        (583.29, 0.21),
        (591.31, 0.18),
        (595.23, 0.07),
    ),
    (
        (2.10, 0.02),
        (2.33, 0.06),
        (3.03, 0.10),
        (3.36, 0.13),
        (3.67, 0.23),
        (3.93, 0.36),
        (4.55, 0.08),
        (5.62, 0.02),
    )
)

colza = Plant(
    PlantType.COLZA,
    (
        (1586.67, 0.05),
        (1600.00, 0.06),
        (1623.34, 0.10),
        (1656.88, 0.13),
        (1699.89, 0.20),
        (1710.96, 0.21),
        (1733.45, 0.18),
        (1811.00, 0.07),
    ),
    (
        (1.58, 0.02),
        (1.79, 0.06),
        (1.98, 0.10),
        (2.23, 0.13),
        (2.46, 0.23),
        (2.88, 0.36),
        (3.19, 0.08),
        (4.46, 0.02),
    )
)

fields = [
    Field(10),
    Field(12),
    Field(8),
    Field(20),
]

plants = [
    barley,
    wheat,
    oat,
    colza
]

plants_ids = list(range(len(plants)))

fields_count = len(fields)
plants_count = len(plants)

plants_variants = get_all_combinations_with_repetition(
    plants_ids, fields_count)

results = get_simulation_results(fields, plants, plants_variants, SIM_COUNT)
save_results_to_csv(results)
