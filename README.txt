README

Huge credit to Benjamin Murphy for all the base work on kriging in python. The following code is simply additions to that code for a specific project.
His code can be seen here: https://github.com/bsmurphy/PyKrige


Weather Kriging

Included in Folder:
pykrige.zip
FinalKrige.py
KrigeFunctions.py
AdditionalCode.py
config.py
database.ini
2011_Meso_All_Metrics.csv
StateBoundingBoxes.csv


GETTING STARTED
This code was written to run on python 3.6
The code connects to a database database not publicly available.

Assuming you have basic panda libraries installed (numpy, pandas, etc.) you will also need to run:
pip install geopandas
pip install pykrige

Historically, there have been some issues with pip install pykrige not installing all necessary modules.
For this reason, included in this folder is a pykrige.py file which can be placed in the correct directory on your computer. 


EXAMPLE CODE
To begin, open FinalKrige.py. 
This file imports all necessary functions from KrigeFunctions, and will walk you through an example.
Feel free to change the date ranges or metrics specified in this example. 
In order to choose metrics please use the 2011_Meso_All_Metrics.csv file included.
Spelling must match what is in this spreadsheet exactly. 
If any issues with a function arises, you can find all of the code in KrigeFunctions.py
The code does take several minutes to run.
The final outputs (details.csv and ascii files, will be placed inside the Krige Functions folder)


AdditionalCode.py can be mainly ignored.
It includes additional code that was used in the creation of these files,
as well as the start of functions that were never finalized.



