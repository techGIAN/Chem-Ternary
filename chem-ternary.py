# import packages
import pandas as pd
import numpy as np
import sys
import os
import matplotlib.pyplot as plt
import ternary

# =========================================
# Internal Parameters
# =========================================

plot_types = {1:'pyroxene', 2:'plagioclase'}
compositions = {1:['Fs', 'Wo', 'En'], 2:['Ab', 'Or', 'An']}

# =========================================
# Helper Methods
# =========================================
def parser(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s.replace("'","")

def str_bool(name, value):
    truthies = ['true', 't', 'yes', 'y', 1]
    falsies = ['false', 'f', 'no', 'n', 0]
    v = value.lower()
    if v in truthies:
        return True
    if v in falsies:
        return False
    error_msg = 'Value ' + str(value) + ' is invalid for parameter ' + name + '.\n' + 'Check ' + paramfile + ' file again.\n' + 'Program exitting...'
    print_error(error_msg)

def type_of_plot(sample, dataframe_list):
    sample = sample.lower()
    i = 1
    for df in dataframe_list:
        ds = df[df['sample'] == sample].reset_index().drop(['index'], axis=1)
        if ds.shape[0] > 0:
            break
        i += 1
    if i > len(plot_types):
        err_msg = 'The sample ' + sample + ' is not found in the dataset ' + datafile + '.\n' + 'Check either the parameter file ' + paramfile + ' or the dataset ' + datafile + '.\n' + 'Program exitting...'
        print_error(err_msg)
    return (i, ds)

def print_error(err):
    print(err)
    exit()

# =========================================
# Main
# =========================================

# import data and drop nan values
datafile = sys.argv[1]
paramfile = sys.argv[2]

# read data
pyro_df = pd.read_excel(datafile, sheet_name='pyroxene').dropna()
plag_df = pd.read_excel(datafile, sheet_name='plagioclase').dropna()
dataframes = [pyro_df, plag_df]
# temp_dataframes = dataframes

# extract the parameters
params = dict()
with open(paramfile) as lines:
    for line in lines:
        # remove spaces or comments in parameter file
        line = line.strip()
        if line == '' or line != '' and line[0] == '#':
            continue

        l = line.split("=")
        l[0] = l[0].strip()
        l[1] = l[1].strip()
        params[l[0]] = parser(l[1])
        if '[' in l[1]:
            temp_list = l[1].replace(' ','').replace("'","").strip("][").split(',')
            final_list = [parser(x) for x in temp_list]
            params[l[0]] = final_list
        if l[0] in ['gridlines', 'show_title', 'show_axes', 'show_legend', 'save_plot']:
            params[l[0]] = str_bool(l[0], l[1])

# save plots as file?
if params['save_plot']:
    filepath = params['directory'] if params['directory'] != '' else './ternary-composition-plots'
    filepath = filepath + '/' if filepath[-1] != '/' else filepath

    # creates the directory if it's not there
    if not os.path.exists(filepath):
        os.mkdir(filepath)
    # rewrites the older directory if it's there but only if save_overwrite = True
    elif os.path.exists(filepath) and params['save_overwrite']:
        file_list = os.listdir(filepath)
        for fs in file_list:
            os.remove(filepath + fs)

# need to check if the sample is in our dataset
samples = params['sample']

for sample in samples:
    ternary_plot_type, df = type_of_plot(sample, dataframes)
    plottype = plot_types[ternary_plot_type]
    comp = compositions[ternary_plot_type]
    
    df[comp] = df[comp] * 100

    ## Boundary and Gridlines
    scale = params['scale']
    figure, tax = ternary.figure(scale=scale)

    # Draw Boundary and Gridlines
    tax.boundary(linewidth=params['boundary_width'])
    if params['gridlines']:         # draw grid only if needed
        tax.gridlines(color=params['gridline_colors'][0], multiple=params['multiple'], linewidth=params['gridline_linewidths'][0])
        tax.gridlines(color=params['gridline_colors'][1], multiple=params['multiple'], linewidth=params['gridline_linewidths'][1])

    # Set ticks
    tax.ticks(axis='lr', linewidth=params['tick_width'], multiple=params['tick_multiple'], offset=params['tick_offset'], clockwise=(plottype=='plagioclase'))
    tax.ticks(axis='b', linewidth=params['tick_width'], multiple=params['tick_multiple'], offset=params['tick_offset'])

    # Set Axis labels and Title
    if params['show_title']:
        title = plottype[0].upper() + plottype[1:] + ' for ' + sample[0].upper() + sample[1:].lower() + '\n' if params['axis_title'].strip() == '' else params['axis_title'] + '\n'
        tax.set_title(title, fontsize=params['fontsize_title'])
    if params['show_axes']:
        ax_labels = params['axes'] if any(params['axes']) else comp
        pa = len(ax_labels)-1
        tax.bottom_axis_label(ax_labels[0], fontsize=params['fontsize_axes'], offset=params['offset_axes'])
        tax.right_axis_label(ax_labels[min(1, pa)], fontsize=params['fontsize_axes'], offset=params['offset_axes'])
        tax.left_axis_label(ax_labels[min(2, pa)], fontsize=params['fontsize_axes'], offset=params['offset_axes'])
    
    # Scatterplots
    algorithms = df['algorithm'].tolist()
    for i in range(df.shape[0]):
        points = [tuple(df.loc[i, comp])]
        tax.scatter(points, marker=params['markers'][min(i,len(params['markers'])-1)], 
                    color=params['markercolors'][min(i,len(params['markercolors'])-1)],
                    s=params['markersizes'][min(i, len(params['markersizes'])-1)], label=algorithms[i])
        if params['show_legend']:
            tax.legend()

    # Background color
    tax.set_background_color(color=params['bg_color'], alpha=params['bg_alpha']) # the detault, essentially

    # Remove default Matplotlib Axes
    tax.clear_matplotlib_ticks()
    tax.get_axes().axis('off')

    figure.set_size_inches((params['area_size_width'], params['area_size_height']))

    if params['save_plot']:
        filename = filepath + 'ternary-composition-' + sample.lower() + '.png'
        ternary.plt.savefig(filename)

    ternary.plt.show()