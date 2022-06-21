import time

vehicles = [
    {
        'id': 0,
        'registration_no': 'na13nru',
        'mobile': '8290380826',
        'name': 'Shivesh Kaundinya'
    },
    {
        'id': 1,
        'registration_no': 'gx150gj',
        'mobile': '1234567890',
        'name': 'Vishwas Modi'
    }
]

entries = []


def registerEntry(registration_no):
    entry_vehicle = None
    for vehicle in vehicles:
        if vehicle['registration_no'] == registration_no:
            entry_vehicle = vehicle
            break

    if entry_vehicle is None:
        print('No corresponding vehicle found in database')
        return

    new_entry = {}
    new_entry['vehicle_id'] = entry_vehicle
    new_entry['time'] = time.time()

    entries.append(new_entry)
    print(f'Vehicle entry registered: {entry_vehicle["registration_no"]}')

    notifyOwner(entry_vehicle)


def notifyOwner(vehicle):
    print(f'Sending entry SMS to {vehicle["mobile"]}')
