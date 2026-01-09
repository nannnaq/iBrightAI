tac_options = [
    {'value': 0.00, 'label': 'T0'},
    {'value': 0.50, 'label': 'T1'},
    {'value': 0.75, 'label': 'T2'},
    {'value': 1.00, 'label': 'T3'},
    {'value': 1.25, 'label': 'T4'},
    {'value': 1.50, 'label': 'T5'},
    {'value': 1.75, 'label': 'T6'},
    {'value': 2.00, 'label': 'T7'},
    {'value': 2.25, 'label': 'T8'},
    {'value': 2.50, 'label': 'T9'},
    {'value': 2.75, 'label': 'T10'},
    {'value': 3.00, 'label': 'T11'},
    {'value': 3.25, 'label': 'T12'},
    {'value': 3.50, 'label': 'T13'},
    {'value': 3.75, 'label': 'T14'},
    {'value': 4.00, 'label': 'T15'},
    {'value': 4.25, 'label': 'T16'},
    {'value': 4.50, 'label': 'T17'},
    {'value': 4.75, 'label': 'T18'}
]

ace_position_options = [
    {'value': -0.25, 'label': 'E0'},
    {'value': -0.50, 'label': 'E1'},
    {'value': -0.75, 'label': 'E2'},
    {'value': -1.00, 'label': 'E3'},
    {'value': 0.00, 'label': 'E-1'}
]

side_arc_position_options = [
    {'value': 16.8, 'label': '+2'},
    {'value': 12.8, 'label': '+1'},
    {'value': 8.8, 'label': '+0'},
    {'value': 4.8, 'label': '-1'}
]

ac_arc_options = [round(i * 0.25 + 35, 2) for i in range(int((55 - 35) / 0.25) + 1)]
reverse_arc_height_options = [round(-45 + i * 5, 1) for i in range(int((55 - (-45)) / 5) + 1)]