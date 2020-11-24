import random
import pandas as pd
import GoogleVRP
import GoogleDistanceMatrix
import API
import numpy as np

def tripAssign(day,hour,minute,timeParameter,store_df, storeLatLon, riderStatus,order,store_output_df):
    if len(store_df) > 0:
        if len(store_df) >1:
            adderess = [storeLatLon] + store_df['DeliveryLatLon'].values.tolist()
            distance_matrix = GoogleDistanceMatrix.get_distance_matrix(API.key, adderess)
            # distance_matrix = (np.array(distance_matrix)*timeParameter).tolist()
            time_window_point = [int(round(i+0.6)) for i in store_df['timeWindow'].values]
            zeros = [int(i) for i in np.zeros(len(store_df))]
            time_window_matrix = [(int(0),int(0))]+list(zip(zeros,time_window_point))

#             if no rider available, assign orders to the next slot
            if len([key for key in riderStatus.keys() if riderStatus[key] == 0]) > 0:
                total_rider = len([key for key in riderStatus.keys() if riderStatus[key] == 0])


                vehicle_route,vehicle = \
                GoogleVRP.VRPTW(distance_matrix,time_window_matrix,1)
                if total_rider > vehicle:
                    selectRider = random.sample([key for key in riderStatus.keys() 
                                             if riderStatus[key] == 0], vehicle)
                else:
                    selectRider = [key for key in riderStatus.keys() 
                         if riderStatus[key] == 0] + ['3rd']*(vehicle-total_rider)


                departure_time = pd.to_datetime('2020-11-0%s %s:%s:00'%(day,hour,str(minute).zfill(2)))

                for ind,rider in enumerate(selectRider):
                    if rider in riderStatus:
                        back_time = departure_time + pd.Timedelta(distance_matrix[vehicle_route[ind][-2]][0], 'seconds')*timeParameter
                        riderStatus[rider] = back_time

                node_deliver_sequnce = []
                node_deliver_time = []
                for vehicle_no in vehicle_route.keys():
                    time = 0

                    for ind,node in enumerate(vehicle_route[vehicle_no]):
                        if node == 0:
                            next
                        else:
                            if ind == 0:
                                time = distance_matrix[0][node]*timeParameter + time
                                node_deliver_time += [time]
                                node_deliver_sequnce += [node]
                            else:
                                time = distance_matrix[vehicle_route[vehicle_no][ind]-1][node] + time
                                node_deliver_time += [time]
                                node_deliver_sequnce += [node]

                node_deliver_time_dict = dict(zip(node_deliver_sequnce,node_deliver_time))
                node_deliver_time_dict = {k : node_deliver_time_dict[k] for k in sorted(node_deliver_time_dict)}
                node_deliver_time = node_deliver_time_dict.values()

                store_df['tripTime'] = node_deliver_time
                # if only one select rider, then length does not match
                if len(selectRider) > 1:

                    rider_assign = np.zeros(len(store_df)+1).tolist()
                    for riderKey in vehicle_route.keys():
                        # key in route is vehicle index
                        rider_no = selectRider[riderKey]
                        for location in vehicle_route[riderKey]:
                            rider_assign[location] = rider_no
                    store_df['rider'] = rider_assign[1:]
                else:

                    store_df['rider'] = selectRider[0]

                store_output_df = pd.concat([store_output_df,store_df])
                
            else:
                order.loc[(order['hour']==hour)&(order['min']==minute)]['dalay'] = 1
                if minute == 55:
                    order.loc[(order['hour']==hour)&(order['min']==minute)]['hour'] = hour+1
                    order.loc[(order['hour']==hour)&(order['min']==minute)]['min'] = 0
                else:
                    order.loc[(order['hour']==hour)&(order['min']==minute)]['min'] = minute + 5
                            # only 1 order
        elif len(store_df) == 1:
            store_df['departureTimeSimulation'] = store_df['departureTime']
            tripDurationReal = store_df['tripDurationReal'].values[0]
            departure_time = store_df['departureTime'].values[0]
            back_time = pd.to_datetime(departure_time) + pd.Timedelta(tripDurationReal*2, 'seconds')
            if len([key for key in riderStatus.keys() if riderStatus[key] == 0]) > 0:
                selectRider = random.sample([key for key in riderStatus.keys() if riderStatus[key] == 0], 1)[0]
            else:
                selectRider = '3rd'
            if selectRider in riderStatus:
                riderStatus[selectRider] = back_time
            store_df['tripTime'] = tripDurationReal
            store_df['rider'] = selectRider
            store_output_df = pd.concat([store_output_df,store_df])

    return (store_output_df,riderStatus,order)
