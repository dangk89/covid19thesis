# covid19thesis

This repository is a project created to crawl and manipulate reddit data for Elizabeth Havers-Christensens master thesis.

The project contains both a python (ThesisScript.py) file and a Juptyer Notebook (ThesisScript.ipynb) file. Both files contain the same code, but the .py File has been cleaned up and edited so it can be executed easily and without the Conda/Jupyter setup.

The crawler took approximately 10 hours to collect all the reddit data. To avoid crawling the same data again, the raw df can be downloaded as a single file using link below. Place the file in the data folder:

https://www.dropbox.com/s/lwhh3cio6z3atvu/df?dl=0

# Running the ThesisScript.py
The ThesisScript.py file should be run from the command line using: "python -i ThesisScript.py" in order to interact with the different methods.

List of available methods for the interactive .py file.

- Crawler - To run test crawler do:
        'df = crawler(dateTuples, searchwords, subreddits, True)'
- Crawler - To run full crawler do:
        'df = crawler(dateTuples, searchwords, subreddits, False)'. Warning: Takes ~10 hours to finish
- Load data - If crawler has executed, or df file exists, just load raw psaw data from file:
        'df = loadExistingDf()'
- Clean data - Clean the loaded dataframe with:
        'newDf = applyCleaning(df)'
- Export data - Export the cleaned data to txt file for sketchengine:
        'exportCommentsToTxt(newDf)'
- Keyness analysis: Calculate keyness scores using existing file with frequency per million and save to csv. Do:
        'keynessAnalysis()'
- Frequency analysis. Frequency of each searchword each month. Save plot and data to file. Do:
        'frequencyAnalysis(newDf, dateTuples)'