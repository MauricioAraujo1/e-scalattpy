# # comando para executar: python app.py

from flask import Flask, request, jsonify
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, LpStatus, value, LpBinary
from tabulate import tabulate

app = Flask(__name__)

@app.route('/optimize', methods=['POST'])
def optimize():
    data = request.json
    restrictions = data.get('restrictions')  # Não está sendo usado na lógica atual, mas pode ser incorporado se necessário
    max_activities = data.get('maxActivities')  # Não está sendo usado na lógica atual
    min_activities = data.get('minActivities')  # Não está sendo usado na lógica atual

    # Entradas do usuário através da API
    num_Tp_variables = int(data.get('num_Tp_variables', 0))
    num_Re_variables = int(data.get('num_Re_variables', 0))
    num_Di_variables = int(data.get('num_Di_variables', 0))

    Tp_names = data.get('Tp_names', [])
    Tp_values = data.get('Tp_values', [])
    Re_values = data.get('Re_values', [])
    Di_values = data.get('Di_values', [])

    # Calcular soma dos produtos e variáveis binárias
    sum_by_Re, sum_binary_by_Re_and_combination = compute_sum_of_products_by_Re(Tp_values, Tp_names, Re_values, Di_values)

    # Diferencas entre valores consecutivos de Re
    total_difference = 0
    for i, Re in enumerate(Re_values[:-1]):
        next_Re = Re_values[i + 1]
        difference = sum_by_Re[Re] - sum_by_Re[next_Re]
        total_difference += difference

    # Problema de otimização
    prob = LpProblem("MaximizeTotalSum", LpMaximize)
    prob += -1 * (total_difference)

    # Restrições de diferença e soma binária
    for i, Re in enumerate(Re_values[:-1]):
        next_Re = Re_values[i + 1]
        prob += sum_by_Re[Re] - sum_by_Re[next_Re] >= 0

    for Tp_name in Tp_names:
        for Di in Di_values:
            prob += lpSum(sum_binary_by_Re_and_combination[Re][(Tp_name, Di)] for Re in Re_values) == 1

    for Di in Di_values:
        for Re in Re_values:
            prob += lpSum(sum_binary_by_Re_and_combination[Re][(Tp_name, Di)] for Tp_name in Tp_names) <= 1

    for Re, sum_value in sum_by_Re.items():
        prob += sum_value >= 0

    prob += lpSum(sum_by_Re.values()) >= 0

    # Resolver o problema
    prob.solve()

    # Resultados
    results = {
        "status": LpStatus[prob.status],
        "total_sum": value(prob.objective),
        "sums_by_Re": {Re: sum([sum_binary_by_Re_and_combination[Re][(Tp_name, Di)].varValue * float(Tp_values[Tp_names.index(Tp_name)]) for Tp_name in Tp_names for Di in Di_values]) for Re in Re_values},
        "total_difference": total_difference,
        "binary_variables": {Re: {(Tp, Di): variable.varValue for (Tp, Di), variable in sum_binary_by_Re_and_combination[Re].items()} for Re in sum_binary_by_Re}
    }

    return jsonify(results)

# Funções para receber valores e nomes
def get_variable_values(variable_name, num_variables):
    values = []
    for i in range(num_variables):
        value = input("Enter the value for {} {}: ".format(variable_name, i+1))
        values.append(value)
    return values

def get_variable_names(variable_name, num_variables):
    names = []
    for i in range(num_variables):
        name = input("Enter the name for {} {}: ".format(variable_name, i+1))
        names.append(name)
    return names

# Função para calcular a soma dos produtos por Re e criar variáveis binárias
def compute_sum_of_products_by_Re(Tp_values, Tp_names, Re_values, Di_values):
    sum_by_Re = {}
    sum_binary_by_Re_and_combination = {}
    for Re in Re_values:
        sum_by_Re[Re] = 0
        sum_binary_by_Re_and_combination[Re] = {}
        for Tp_name, Tp in zip(Tp_names, Tp_values):
            for Di in Di_values:
                sum_binary_by_Re_and_combination[Re][(Tp_name, Di)] = LpVariable(f"binary_{Tp_name}_{Di}_{Re}", 0, 1, LpBinary)
                sum_by_Re[Re] += float(Tp) * sum_binary_by_Re_and_combination[Re][(Tp_name, Di)]
    return sum_by_Re, sum_binary_by_Re_and_combination

if __name__ == '__main__':
    app.run(debug=True)






# from flask import Flask, request, jsonify
# from pulp import LpProblem, LpMaximize, LpVariable, lpSum, LpStatus, value, LpBinary
# from tabulate import tabulate

# app = Flask(__name__)

# # Funções para receber valores e nomes
# def get_variable_values(variable_name, num_variables):
#     values = []
#     for i in range(num_variables):
#         value = input("Enter the value for {} {}: ".format(variable_name, i+1))
#         values.append(value)
#     return values

# def get_variable_names(variable_name, num_variables):
#     names = []
#     for i in range(num_variables):
#         name = input("Enter the name for {} {}: ".format(variable_name, i+1))
#         names.append(name)
#     return names

# # Função para calcular a soma dos produtos por Re e criar variáveis binárias
# def compute_sum_of_products_by_Re(Tp_values, Tp_names, Re_values, Di_values):
#     sum_by_Re = {}
#     sum_binary_by_Re_and_combination = {}
#     for Re in Re_values:
#         sum_by_Re[Re] = 0
#         sum_binary_by_Re_and_combination[Re] = {}
#         for Tp_name, Tp in zip(Tp_names, Tp_values):
#             for Di in Di_values:
#                 sum_binary_by_Re_and_combination[Re][(Tp_name, Di)] = LpVariable(f"binary_{Tp_name}_{Di}_{Re}", 0, 1, LpBinary)
#                 sum_by_Re[Re] += float(Tp) * sum_binary_by_Re_and_combination[Re][(Tp_name, Di)]
#     return sum_by_Re, sum_binary_by_Re_and_combination

# # Entradas
# num_Tp_variables = int(input("Enter the number of Tp variables: "))
# num_Re_variables = int(input("Enter the number of Re variables: "))
# num_Di_variables = int(input("Enter the number of Di variables: "))

# Tp_names = get_variable_names("Tp", num_Tp_variables)
# Tp_values = get_variable_values("Tp", num_Tp_variables)
# Re_values = get_variable_values("Re", num_Re_variables)
# Di_values = get_variable_values("Di", num_Di_variables)

# # Calcular soma dos produtos e variáveis binárias
# sum_by_Re, sum_binary_by_Re_and_combination = compute_sum_of_products_by_Re(Tp_values, Tp_names, Re_values, Di_values)

# # Diferencas entre valores consecutivos de Re
# total_difference = 0
# for i, Re in enumerate(Re_values[:-1]):
#     next_Re = Re_values[i + 1]
#     difference = sum_by_Re[Re] - sum_by_Re[next_Re]
#     total_difference += difference

# # Problema de otimização
# prob = LpProblem("MaximizeTotalSum", LpMaximize)
# prob += -1 * (total_difference)

# # Restrições de diferença e soma binária
# for i, Re in enumerate(Re_values[:-1]):
#     next_Re = Re_values[i + 1]
#     prob += sum_by_Re[Re] - sum_by_Re[next_Re] >= 0

# for Tp_name in Tp_names:
#     for Di in Di_values:
#         prob += lpSum(sum_binary_by_Re_and_combination[Re][(Tp_name, Di)] for Re in Re_values) == 1

# for Di in Di_values:
#     for Re in Re_values:
#         prob += lpSum(sum_binary_by_Re_and_combination[Re][(Tp_name, Di)] for Tp_name in Tp_names) <= 1

# for Re, sum_value in sum_by_Re.items():
#     prob += sum_value >= 0

# prob += lpSum(sum_by_Re.values()) >= 0

# # Escolha do usuário para definir variáveis binárias específicas
# if input("Do you want to set a binary variable? (yes/no): ") == "yes":
#     answer = "yes"
#     while answer == "yes":
#         Tp_choice = input("Select Tp name: ")
#         Di_choice = input("Select Di: ")
#         Re_choice = input("Select Re: ")
#         binary_value = int(input("Enter binary value (0 or 1): "))
#         prob += sum_binary_by_Re_and_combination[Re_choice][(Tp_choice, Di_choice)] == binary_value
#         answer = input("Do you want to set another binary value? (yes/no): ")

# # Restrições baseadas em regras específicas de Tp
# if input("Do you want to define a rule after a Tp? (yes/no): ") == "yes":
#     answer2 = "yes"
#     while answer2 == "yes":
#         Defined_Tp_name = input("Select the Tp name: ")
#         for k, Re in enumerate(Re_values):
#             for j, Tp_name in enumerate(Tp_names):
#                 if Tp_name == Defined_Tp_name:
#                     for i, Di in enumerate(Di_values[:-1]):
#                         current_condition = sum_binary_by_Re_and_combination[Re][(Tp_name, Di)]
#                         next_Di = Di_values[i + 1]
#                         sum_next_combinations = lpSum(sum_binary_by_Re_and_combination[Re][(next_Tp, next_Di)] for next_Tp in Tp_names)
#                         prob += current_condition + sum_next_combinations <= 1
#         answer2 = input("Do you want to define another rule after a Tp? (yes/no): ")

# # Resolver o problema
# prob.solve()

# # Resultados
# print("Optimization Status:", LpStatus[prob.status])
# print("Total sum of products for all Re:", value(prob.objective))

# for Re, sum_value in sum_by_Re.items():
#     total_sum_by_Re = sum([sum_binary_by_Re_and_combination[Re][(Tp_name, Di)].varValue * float(Tp_values[Tp_names.index(Tp_name)]) for Tp_name in Tp_names for Di in Di_values])
#     print("Total sum of products for Re {}: {}".format(Re, total_sum_by_Re))

# total_difference_output = 0
# for i, Re in enumerate(Re_values[:-1]):
#     next_Re = Re_values[i + 1]
#     total_sum_by_Re = sum([sum_binary_by_Re_and_combination[Re][(Tp_name, Di)].varValue * float(Tp_values[Tp_names.index(Tp_name)]) for Tp_name in Tp_names for Di in Di_values])
#     next_total_sum_by_Re = sum([sum_binary_by_Re_and_combination[next_Re][(Tp_name, Di)].varValue * float(Tp_values[Tp_names.index(Tp_name)]) for Tp_name in Tp_names for Di in Di_values])
#     difference = total_sum_by_Re - next_total_sum_by_Re
#     print("Difference from Re {} to Re {}: {}".format(Re, next_Re, difference))
#     total_difference_output += difference
# print("Total Difference between consecutive Re's:", total_difference_output)

# print("\nBinary Variables:")
# for Re, combination_dict in sum_binary_by_Re_and_combination.items():
#     print("Re:", Re)
#     for (Tp, Di), variable in combination_dict.items():
#         print(f"Di: {Di}, Tp: {Tp} - Value: {variable.varValue}")

# table_data = [["" for _ in range(len(Re_values) + 1)] for _ in range(len(Di_values) * len(Tp_values) + 1)]
# table_data[0][0] = "Di/Tp"
# for i, Re in enumerate(Re_values):
#     table_data[0][i + 1] = f" {Re}"
# for i, Di in enumerate(Di_values):
#     for j, Tp_name in enumerate(Tp_names):
#         table_data[i * len(Tp_values) + j + 1][0] = f" {Di}, {Tp_names[j]}"
#         for k, Re in enumerate(Re_values):
#             Corresp_Tp = Tp_values[j]
#             table_data[i * len(Tp_values) + j + 1][k + 1] = sum_binary_by_Re_and_combination[Re][(Tp_name, Di)].varValue * float(Corresp_Tp)

# print("\nResults Table:")
# print(tabulate(table_data, headers="firstrow", tablefmt="grid"))


