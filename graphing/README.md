# Experimental results

The data from the experiments shown in our paper can be downloded [here](https://doi.org/10.5281/zenodo.10063011)

The dataset is composed of the following subfolders:

- scatter-baseline: system log data used to generate figure 2
- scatter-cloud: system log data used to generate figure 4
- scatter-scaling: system log data used to generate figure 3
- scatterpp-baseline: system log data used to generate figure 6
- scatterpp-scaline-10: system log data used to generate figure 7 and 8

# Analysis and Graphing with Jupyter Notebooks

As part of our paper, we used two notebooks to produce the graphs found in our final manuscript:

1. `processing.ipynb`, which was used to perform the pre-processing on the data log files produced by `scAtteR` and `scAtteR++`, and `Oakestra`. The script generates .csv files of the pre-processed log data to be used by the following notebook.
2. `graphs-<experiment-name>.ipynb`, which was used to read the .csv files and then create the graphs 

All notebooks can be run in a cell-by-cell fashion, but modifications are required to the files so that data is read and analysed properly.

## Processing

1. The `base_path` variable is a string which should point to the root folder containing the data folders of the experiments performed.
2. The `experiments` variable is a list which contains the specific names of the experiments/data folders to be pre-processed. By default all folders in the dataset are executed.

All the cells can then be run in order from the top of the notebook to the bottom. Once the final cell begins executing and the log files are being analysed, .csv data files will be generated, which can be loaded by the graphing notebook.

## Graphing 

Each `graphs-<experiment-name>.ipynb` plots the result of the data folder with the corresponding name. Note that the pre-processing (previous section) must be performed before the plot. 

1. The `path` string variable should point to the location of where the processed .csv files are.
2. The `graphs` dictionary/JSON structure contains the details of the graphs to be created. This can be customized to change the plot shape and type. The following is an example with comments explaining the general structure. 

```python
graphs = {
    "graph1": {
        "name": "edge", # file name
        "data": ["scatter-baseline"], # name of corresponding folder of results
        "permutation_order": [1, 0, 3, 2], # for rearranging the order of the experiment permutations
        "plots": {
            "plot1": {
                "legends": { # size of the legends used for the permutations legend, and list of services
                    "exp": [0, 1.2, 1, 0.2], 
                    'services': [0, 1.2, 1, 0.2],
                },
                "legend_cols": 2,
                'legend_size': 20,
                "figsize": [15, 10],
                "height_ratios": [1, 1, 1, 1],
                "subplots": (3, 2),
                "graphs": { # subplots and their related graphing parameters
                    "graph0": {
                        "name": "FPS",
                        "results_key": "fps",
                        "graph_index": 0,
                        "subplot_loc": (0,0),
                        "filler": False,
                        "y_axis_lims": [0, 32],
                        "y_tick_marks": [0, 31, 10],
                    },
                }
            }
        }
    }
}
```

Same as with the processing notebook, the cells in the grapher can be run from the top down. The final cell contains code which loops through the defined `graphs` structure and tries to locate the correct data from the .csv files to then create output graphs stored in a folder called `graphs_conext` (this should be created or the path changed)
