import random
from math import sqrt
from enum import Enum
from itertools import product

STD_NORM_05 = 1.96
STD_NORM_10 = 1.65

SIM_COUNT = 10000
SIM_OVERSIZED_MULT = 0.5


class PlantType(Enum):
    BARLEY = 'BARLEY'
    WHEAT = 'WHEAT'
    OAT = 'OAT'
    COLZA = 'COLZA'
    CORN = 'CORN'


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
        PlantType.CORN: {
            "max": 40,
            "produced": 0
        }
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
        self.price_per_ton = None

    def set_random_price_per_ton(self):
        self.price_per_ton = take_value_from_dist(self.price_per_ton_dist)

    def get_price_per_ton(self):
        return self.price_per_ton

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
    def __init__(self, iterations: int, fields: list, plants: list, plants_variant: list):
        self.fields = fields
        self.plants_variant = plants_variant
        self.plants = list(map(lambda id: plants[id], plants_variant))

        fields[0].ha
        self.iterations = iterations
        self.cases = []
        self.sum = 0.0
        self.average_income = 0.0
        self.max_income = 0.0
        self.min_income = float('inf')
        self.std_dev_income = 0.0
        self.left_conf_interval = 0.0
        self.right_conf_interval = 0.0

    def run_simulation(self):
        fields = self.fields
        plants = self.plants

        for _ in range(self.iterations):
            sell_limitations = create_sell_limitations()

            for plant in plants:
                plant.set_random_price_per_ton()

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
        plant_price_per_ton = plant.get_price_per_ton()
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
        s = (
            "Iterations {}\n" + "Names {}\n" + "Average Income {}\n" +
            "Std. Dev. Income {}\n"+"Max Income {}\n" +
            "Min Income {}\n" + "Left conf {}\n" + "Right conf {}\n"
        )
        return s.format(
            self.iterations, self.get_plants_variant_names(),
            self.average_income, self.std_dev_income, self.max_income,
            self.min_income, self.left_conf_interval,
            self.right_conf_interval)

    def get_plants_variant_names(self):
        return " ".join(list(map(lambda x: x.type.name, self.plants)))


def map_plants_ids_to_plants(plants_ids):
    return


def get_simulation_results(fields, plants, plants_variants, simulations_count):
    results = []
    print("Running simulations for {} fields, and {} plants, with total variants of {}".format(
        fields_count, plants_count, len(plants_variants)))
    for plant_variant in plants_variants:
        random.seed(59012)  # TODO: Napisać w docu LUL
        simulation = Simulation(
            simulations_count, fields, plants, plant_variant)
        simulation.run_simulation()
        results.append(simulation)

    results_sorted = sorted(
        results, key=lambda sim: sim.average_income, reverse=True)
    print("Simulations ended")
    return results_sorted


def generate_comparison_matrice_from_results(results):
    avg_comparison_matrice = []
    for i in range(len(results)):
        comparison_row = []
        for j in range(len(results)):
            # Przedziały ufności
            if (
                results[i].right_conf_interval < results[j].left_conf_interval or
                results[i].left_conf_interval > results[j].right_conf_interval
            ):
                # Przedziały ufności na siebie nie zachodzą, porównujemy średnie
                i_is_greater_than_j_raw = (
                    results[i].average_income > results[j].average_income)
                comparison_row.append(1 if i_is_greater_than_j_raw else 0)
            else:
                # Przedziały ufności na siebie zachodzą
                comparison_row.append(0)
        avg_comparison_matrice.append(comparison_row)
    return avg_comparison_matrice


def generate_results_file(results):
    print("Saving results...")
    with open('results.csv', 'w') as f:
        header = ("VARIANT,AVG,MIN,MAX,STD DEV,LEFT CONF,RIGHT CONF\n").format()
        lines = [header]
        for result in results:
            line = "{},{},{},{},{},{},{}\n".format(
                result.get_plants_variant_names(),
                result.average_income,
                result.min_income,
                result.max_income,
                result.std_dev_income,
                result.left_conf_interval,
                result.right_conf_interval
            )
            lines.append(line)
        f.writelines(lines)


def generate_comparison_matrice_file(results, comparison_matrice):
    print("Saving comparisons matrice...")
    with open('comparisons.csv', 'w') as f:
        header = ",".join(
            map(lambda result: result.get_plants_variant_names(), results))
        lines = ["," + header + ",BETTER THAN COUNT" + "\n"]
        for i in range(len(comparison_matrice)):
            line = "{},{},{}".format(
                results[i].get_plants_variant_names(),
                ",".join(list(map(lambda x: str(x), comparison_matrice[i]))),
                str(sum(comparison_matrice[i])),
            )
            lines.append(line + "\n")
        f.writelines(lines)


def generate_calculated_comparison_matrice_file(results, comparison_matrice):
    print("Saving calculated comparisons matrice...")
    with open('comparisons_calculated.csv', 'w') as f:
        header = "VARIANT,BETTER THAN COUNT,INCOME AVG,LEFT CONF,RIGHT CONF\n"
        lines = [header]
        for i in range(len(comparison_matrice)):
            line = "{},{},{},{},{}".format(
                results[i].get_plants_variant_names(),
                sum(comparison_matrice[i]),
                results[i].average_income,
                results[i].left_conf_interval,
                results[i].right_conf_interval
            )
            lines.append(line + "\n")
        f.writelines(lines)


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
        (2.70, 0.10),
        (3.50, 0.13),
        (4.40, 0.25),
        (5.66, 0.35),
        (7.38, 0.13),
        (9.45, 0.04),
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
        (2.67, 0.06),
        (3.11, 0.10),
        (3.56, 0.14),
        (4.22, 0.25),
        (4.72, 0.35),
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
        (2.53, 0.04),
        (3.03, 0.07),
        (3.36, 0.13),
        (3.67, 0.27),
        (3.93, 0.36),
        (4.55, 0.08),
        (5.62, 0.05),
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
        (1.58, 0.06),
        (1.79, 0.08),
        (1.98, 0.12),
        (2.23, 0.15),
        (2.46, 0.27),
        (2.88, 0.23),
        (3.19, 0.07),
        (4.46, 0.02),
    )
)

corn = Plant(
    PlantType.CORN,
    (
        (630.33, 0.05),
        (645.54, 0.13),
        (657.91, 0.18),
        (679.00, 0.24),
        (730.32, 0.26),
        (777.77, 0.07),
        (810.76, 0.07),
    ),
    (
        (6.78, 0.05),
        (6.90, 0.13),
        (7.12, 0.20),
        (7.45, 0.24),
        (8.12, 0.17),
        (9.32, 0.10),
        (11.22, 0.08),
        (13.45, 0.03),
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
    colza,
    corn
]

plants_ids = list(range(len(plants)))

fields_count = len(fields)
plants_count = len(plants)

plants_variants = get_all_combinations_with_repetition(
    plants_ids, fields_count)
results = get_simulation_results(fields, plants, plants_variants, SIM_COUNT)
comparison_matrice = generate_comparison_matrice_from_results(results)

generate_results_file(results)
generate_calculated_comparison_matrice_file(results, comparison_matrice)
generate_comparison_matrice_file(results, comparison_matrice)
# save_results_to_csv(results)
