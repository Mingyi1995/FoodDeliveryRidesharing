"""Vehicles Routing Problem (VRP)."""

from __future__ import print_function
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def create_data_model(distance_matrix,vehicle):
    """Stores the data for the problem."""
    data = {}
    data['distance_matrix'] = distance_matrix
    data['num_vehicles'] = vehicle
    data['depot'] = 0
    return data


def print_solution(distance_matrix,data, manager, routing, solution):
    """Prints solution on console."""
    max_route_distance = 0
    vehicle_route = {}
    vehicle_back_distance = {}
    vehicle_deliver_distance = {}
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        route = []
        while not routing.IsEnd(index):
            # plan_output += ' {} -> '.format(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
            route += [manager.IndexToNode(index)]
            previous_index = index
        # plan_output += '{}\n'.format(manager.IndexToNode(index))
        # plan_output += 'Distance of the route: {}m\n'.format(route_distance)
        vehicle_route[vehicle_id] = route
        vehicle_back_distance[vehicle_id] = route_distance
        trip_distance = route_distance - distance_matrix[route[-1]][0]
        vehicle_deliver_distance[vehicle_id] = trip_distance
        max_route_distance = max(route_distance, max_route_distance)
    # print('Maximum of the route distances: {}m'.format(max_route_distance))
    # print(vehicle_route)
    # print(vehicle_distance)

    return [vehicle_route,vehicle_back_distance,vehicle_deliver_distance]



def VRP(distance_matrix,vehicle):
    """Solve the CVRP problem."""
    # Instantiate the data problem.
    data = create_data_model(distance_matrix,vehicle)

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)


    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint.
    dimension_name = 'Distance'
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        9999999999999999,  # vehicle maximum travel distance
        True,  # start cumul to zero
        dimension_name)
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        vehicle = print_solution(distance_matrix,data, manager, routing, solution)
        return vehicle
    else:
        VRP(distance_matrix,vehicle+1)

### time window

def create_data_model_tw(distance_matrix,time_window_matrix,vehicle):
    """Stores the data for the problem."""
    data = {}
    data['time_matrix'] = distance_matrix
    data['time_windows'] = time_window_matrix
    data['num_vehicles'] = vehicle
    data['depot'] = 0
    return data


def print_solution_tw(distance_matrix,data, manager, routing, solution):
    """Prints solution on console."""
    time_dimension = routing.GetDimensionOrDie('Time')
    total_time = 0
    vehicle_route = {}
    vehicle_back_distance = {}
    vehicle_deliver_distance = {}
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        route = []
        total_time = []
        while not routing.IsEnd(index):
            index = solution.Value(routing.NextVar(index))
            previous_index = index
            time_var = time_dimension.CumulVar(index)
            route += [manager.IndexToNode(index)]
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
            plan_output += '{0} Time({1},{2}) -> '.format(
                manager.IndexToNode(index), solution.Min(time_var),
                solution.Max(time_var))
            
            
        vehicle_route[vehicle_id] = route
        vehicle_back_distance[vehicle_id] = route_distance
        trip_distance = route_distance - distance_matrix[route[-1]][0]
        vehicle_deliver_distance[vehicle_id] = trip_distance
        time_var = time_dimension.CumulVar(index)
        total_time += [solution.Min(time_var)]
#         print(solution.Min(time_var))
    return (vehicle_route,vehicle_back_distance,vehicle_deliver_distance)


def VRPTW(distance_matrix,time_window_matrix,vehicle,total_rider):
    """Solve the VRP with time windows."""
    # Instantiate the data problem.
    data = create_data_model_tw(distance_matrix,time_window_matrix,vehicle)

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data['time_matrix']),
                                           data['num_vehicles'], data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)


    # Create and register a transit callback.
    def time_callback(from_index, to_index):
        """Returns the travel time between the two nodes."""
        # Convert from routing variable Index to time matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['time_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Time Windows constraint.
    time = 'Time'
    routing.AddDimension(
        transit_callback_index,
        30,  # allow waiting time
        999999,  # maximum time per vehicle
        False,  # Don't force start cumul to zero.
        time)
    time_dimension = routing.GetDimensionOrDie(time)
    # Add time window constraints for each location except depot.
    for location_idx, time_window in enumerate(data['time_windows']):
        if location_idx == 0:
            continue
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
    # Add time window constraints for each vehicle start node.
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        time_dimension.CumulVar(index).SetRange(data['time_windows'][0][0],
                                                data['time_windows'][0][1])

    # Instantiate route start and end times to produce feasible times.
    for i in range(data['num_vehicles']):
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.Start(i)))
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.End(i)))

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        vehicle_route,vehicle_back_distance,vehicle_deliver_distance = print_solution_tw(distance_matrix, data, manager, routing, solution)
        # print(type(output))
        return (vehicle_route,vehicle_back_distance,vehicle_deliver_distance,vehicle)
    else:
        # print('no solution')
        vehicle += 1
        # print('vehicle +1')
        if vehicle <= total_rider:
            return VRPTW(distance_matrix,time_window_matrix,vehicle,total_rider)

