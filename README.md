# Scrape and chat with repositories

This project is designed to allow you to plug in a GitHub repository URL (like `https://github.com/soos3d/chatgpt-plugin-development-quickstart-express`) and then engage with OpenAI's Chat GPT models to gain a better understanding of the repository's codebase.

To handle the 'AI' part, the program utilizes the [Langchain](https://python.langchain.com/en/latest/index.html) framework and [Deep Lake](https://docs.activeloop.ai/) following this logic:

1. The repository is scraped, and each file's content is saved in a `txt` format.
2. Langchain is used to load this data, break it down into chunks, and create embedding vectors using the OpenAI embedding model.
3. Langchain then helps to build a vector database using Deep Lake.
4. Lastly, Langchain spins up a chat bot with the help of a Chat GPT model.

With this setup, you can interact with 'chat' with any repository.

## Table of contents

- [Project structure](#project-structure)
- [Requirements](#requirements)
- [Getting Started](#getting-started)
- [Use a cloud vector database](#use-a-cloud-vector-database)
- [Configuration](#configuration)

## Project structure

This project only has three files! Langchain really allows to simply the logic. 

```sh
chat-with-repo-langchain
  │
  ├── main.py
  ├── chat.py
  ├── src
  │   └── scraper.py
  └── .env
```

- `main.py`: This is the entry point and the part responsible for ingesting a repository URL, generating embedding vectors, and indexing it in a vector database.
- `chat.py`: This module starts the chat functionality, accepts user queries, and gets the context from the Vectore database; it also stores the chat history for the time it's running.
- `src/scraper.py`: This file holds the scraping logic, and this module is called during the execution of `main.py`.
- `.env`: This is where environment variables are stored; it also holds the configuration of the vector database.


## Requirements

Before getting started, ensure you have the following:

* [Python](https://www.python.org/downloads/) - Version 3.7 or newer is required.
* An active account on OpenAI, along with an [OpenAI API key](https://platform.openai.com/account/api-keys).
* A Deep Lake account, complete with a [Deep Lake API key](https://app.activeloop.ai/?utm_source=referral&utm_medium=platform&utm_campaign=signup_promo_settings&utm_id=plg).

## Getting Started

> ℹ️ It's strongly advised to create a new Python virtual environment to run this program. It helps maintain a tidy workspace by keeping dependencies in one place.

* Create a Python virtual environment with:

```sh
python3 -m venv repo-ai
```

Then activate it with:

```sh
source repo-ai/bin/activate
```

* Clone the repository:

```sh
git clone https://github.com/soos3d/chat-with-repo-langchain-openai.git
```
Then:

```sh
cd chat-with-repo-langchain-openai
```

* Install the Python dependencies:

```sh
pip install -r requirements.txt
```

This will install all of the required Langchain, OpenAI, and Deep Lake dependencies.

* Edit the `.env.sample` file with your information, specifically the API keys:

```env
# Scraper config
FILES_TO_IGNORE='"package-lock.json", "LICENSE", ".gitattributes", ".gitignore", "yarn.lock"'
SAVE_PATH="./repos_content"     # Save the scraped data in a directory called repos-content in the root
MAX_ATTEMPTS=3

# Repository to scrape if the hardcoded section is active.
REPO_URL="https://github.com/soos3d/chatgpt-plugin-development-quickstart-express"

# OpenAI 
OPENAI_API_KEY="YOUR_KEY"
EMBEDDINGS_MODEL="text-embedding-ada-002"
LANGUAGE_MODEL="gpt-3.5-turbo" # gpt-4

# Deeplake vector DB
ACTIVELOOP_TOKEN="YOUR_KEY"
DATASET_PATH="./local_vector_db" # "hub://USER_ID/custom_dataset"  # Edit with your user id if you want to use the cloud db.
```

Here is where you select which Chat GPT model to use; `gpt-3.5-turbo` it the default model, and the path to the cloud vector dataset if you don't want to store it locally; it is set up locally by default.

* Run the `main.py` file:

```sh
python3 main.py
```

* Input a repository URL

```sh
Input the repository you want to index: https://github.com/soos3d/chatgpt-plugin-development-quickstart-express
```

This will scrape the repository, load the files, split it in chunks, generate embedding vectors, create a local vector database and store the embeddings.

You will see the following response:

```sh
Scraping the repository...

====================================================================================================
Repository contents written to ./repos_content/soos3d_chatgpt-plugin-development-quickstart-express.
====================================================================================================
List of file paths written to ./repos_content/soos3d_chatgpt-plugin-development-quickstart-express/soos3d_chatgpt-plugin-development-quickstart-express_file_paths.txt.

Time needed to pull the data: 10.23s.
====================================================================================================
Loading docs...
 88%|███████████████████████████████████████████████████████████████████████████████████████████▉             | 7/8 [00:01<00:00,  5.79it/s]
Loaded 7 documents.
====================================================================================================
Splitting documents...
Generated 25 chunks.
====================================================================================================
Creating vector DB...
./local_vector_db loaded successfully.
Evaluating ingest: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:05<00:00
Dataset(path='./local_vector_db', tensors=['embedding', 'ids', 'metadata', 'text'])

  tensor     htype     shape      dtype  compression
  -------   -------   -------    -------  ------- 
 embedding  generic  (25, 1536)  float32   None   
    ids      text     (25, 1)      str     None   
 metadata    json     (25, 1)      str     None   
   text      text     (25, 1)      str     None   
Vector database updated.
```

* Chat with the repository:

```sh
python3 chat.py
```

This will start the chat model and you can leverage it's full power, I recomend to use the GPT 4 model if possible. The followinf is an example response based on my [ChatGPT plugins boilerplate repository]() using the `gpt4` model:

```sh
./local_vector_db loaded successfully.

Deep Lake Dataset in ./local_vector_db already exists, loading from the storage
Dataset(path='./local_vector_db', read_only=True, tensors=['embedding', 'ids', 'metadata', 'text'])

  tensor     htype     shape      dtype  compression
  -------   -------   -------    -------  ------- 
 embedding  generic  (25, 1536)  float32   None   
    ids      text     (25, 1)      str     None   
 metadata    json     (25, 1)      str     None   
   text      text     (25, 1)      str     None   

Please enter your question (or 'quit' to stop): Can you explain how the index.js file in the ChatpGTP plugin quickstart repo works?

Question: Can you explain how the index.js file in the ChatpGTP plugin quickstart repo works?
Answer: Certainly! The `index.js` file in the ChatGPT plugin quickstart repository serves as the entry point for the Express.js server application. Here's a breakdown of its functionality:

1. Import required modules: The necessary modules are imported, including `express`, `path`, `cors`, `fs`, and `body-parser`. Additionally, the custom module `getAirportData` is imported from `./src/app`.

```javascript
const express = require('express');
const path = require('path');
const cors = require('cors');
const fs = require('fs');
const bodyParser = require('body-parser');
require('dotenv').config();

const { getAirportData } = require('./src/app');
```
```

2. Initialize Express application: The Express application is initialized and stored in the `app` variable.

```javascript
const app = express();
```

3. Set the port number: The port number is set based on the environment variable `PORT` or defaults to 3000 if `PORT` is not set.

```javascript
const PORT = process.env.PORT || 3000;
```

4. Configure Express to parse JSON: The application is configured to parse JSON in the body of incoming requests using `bodyParser.json()`.

```javascript
app.use(bodyParser.json());
```

5. Configure CORS options: CORS (Cross-Origin Resource Sharing) is configured to allow requests from `https://chat.openai.com` and to send a 200 status code for successful preflight requests for compatibility with some older browsers.

```javascript
const corsOptions = {
  origin: 'https://chat.openai.com',
  optionsSuccessStatus: 200
};

app.use(cors(corsOptions));
```

The rest of the `index.js` file sets up the server to listen on the specified port and handles the routes for the plugin. The server starts listening for incoming requests on the specified port, and the plugin is ready to be used with ChatGPT.

Tokens Used: 2214
        Prompt Tokens: 1817
        Completion Tokens: 397
Successful Requests: 1
Total Cost (USD): $0.07833

```
> ℹ️ Note that it also prints how many tokens were used and an estimate cost for the OpenAI API.

## Use a cloud vector database

By default this project creates a local vector database using [Deep Lake](https://app.activeloop.ai/?utm_source=referral&utm_medium=platform&utm_campaign=signup_promo_settings&utm_id=plg), but you can also use a cloud based DB. 

> Note that e local database will be faster.

In `main.py` uncomment the following section:

```py
    # Enable the following to create a cloud vector DB using Deep Lake
    """
    deeplake_path = os.getenv('DATASET_PATH')
    ds = deeplake.empty(deeplake_path)
    db = DeepLake(dataset_path=deeplake_path, embedding_function=embeddings, overwrite=True, public=True)
    """
```

Remember to edit the environment variable for the dataset path and add the `USER_ID` you have in your [Deep Lake](https://app.activeloop.ai/?utm_source=referral&utm_medium=platform&utm_campaign=signup_promo_settings&utm_id=plg) account, and to remove or comment the code to create the local DB.

```env
DATASET_PATH="hub://USER_ID/custom_dataset"  # Edit with your user id if you want to use the cloud db.
```

```py
    # Set the deeplake_path to the repository name
    deeplake_path = os.getenv('DATASET_PATH')
    db = DeepLake(dataset_path=deeplake_path, embedding_function=embeddings, overwrite=True)
```

## Configuration

The entire app is configured from the `.env` file so you don't have to actually change the code if you don't want to. 

* FILES_TO_IGNORE is a list of files that will not be scraped. This is to reduce clutter and save some resources.

```env
# Scraper config
FILES_TO_IGNORE='"package-lock.json", "LICENSE", ".gitattributes", ".gitignore", "yarn.lock"'
SAVE_PATH="./repos_content"     # Save the scraped data in a directory called repos-content in the root
MAX_ATTEMPTS=3

# Repository to scrape if the hardcoded section is active.
REPO_URL="https://github.com/soos3d/chatgpt-plugin-development-quickstart-express"

# OpenAI 
OPENAI_API_KEY="YOUR_KEY"
EMBEDDINGS_MODEL="text-embedding-ada-002"
LANGUAGE_MODEL="gpt-3.5-turbo" # gpt-4

# Deeplake vector DB
ACTIVELOOP_TOKEN="YOUR_KEY"
DATASET_PATH="./local_vector_db" # "hub://USER_ID/custom_dataset"  # Edit with your user id if you want to use the cloud db.
```