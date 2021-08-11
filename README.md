# Steam Game Recommendation

## Run Instructions

### Prerequisite
* Clone this repository
* Install following python dependencies
    * numpy
    * scikit-learn
    * pandas
    * pytorch
    * rank_bm25
    * fastapi
    * uvicorn[standard]
* Install npm and yarn to run demo frontend

### Experiments
* Run all cells in respective jupyter notebooks under the project root directory.

### Demo Frontend and Backend
* Run `yarn install`
* Run `yarn start` to host the demo frontend
* Run `uvicorn backend.app:app` to launch the backend
