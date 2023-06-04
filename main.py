import sys
sys.path.insert(0, './src')
import os
import time

from dotenv import load_dotenv
from scraper import main as github_scraper_main
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import DeepLake
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
import deeplake

def main():
    """
    Main function that handles the scraping, loading, splitting, vector generation, 
    Optional querying and question-answering process.
    """

    # Load environment variables from .env file
    load_dotenv()
    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    os.environ['ACTIVELOOP_TOKEN'] = os.getenv('ACTIVELOOP_TOKEN')

    #repo_url = os.getenv('REPO_URL')   # Enable this if you want to input the URL from env variables.
    repo_url = input('Input the repository you want to index: ')
    max_attempts = int(os.getenv('MAX_ATTEMPTS', 5))  # Set a default value for max_attempts

    # Config embeddings model

    embeddings = OpenAIEmbeddings(disallowed_special=())

    # Scrape the repo; will create a txt file with the organized data
    for attempt in range(1, max_attempts+1):
        try:
            print('Scraping the repository...\n')
            start_time = time.time()  
            github_scraper_main(repo_url)
            elapsed_time = time.time() - start_time  
            print(f"Time needed to pull the data: {elapsed_time:.2f}s.")
            break  
        except Exception as e:
            print(f"Attempt {attempt} failed with error: {e}")
            if attempt == max_attempts:
                print("Max attempts reached. Exiting...")
                return
            else:
                print("Retrying...")

    # Load the document
    loader = DirectoryLoader('./repos_content/', glob="**/*.txt", show_progress=True, use_multithreading=True)
    print("=" * 100)
    print('Loading docs...')
    docs = loader.load()
    print(f"Loaded {len(docs)} documents.")

    # Split the docs
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=10, length_function=len)
    print("=" * 100)
    print('Splitting documents...')
    text = text_splitter.split_documents(docs)
    print(f'Generated {len(text)} chunks.')

    # Generate vectors and update the vector db.
    print("=" * 100)
    print('Creating vector DB...')

    # Set the deeplake_path to the repository name
    deeplake_path = os.getenv('DATASET_PATH')
    db = DeepLake(dataset_path=deeplake_path, embedding_function=embeddings, overwrite=True)


    # Enable the following to create a cloud vector DB using Deep Lake
    """
    deeplake_path = os.getenv('DATASET_PATH')
    ds = deeplake.empty(deeplake_path)
    db = DeepLake(dataset_path=deeplake_path, embedding_function=embeddings, overwrite=True, public=True)
    """

    db.add_documents(text)
    print('Vector database updated.')

# Enable the following section and edit the questions to test while indexing a new repository.
"""
    # Initialize DeepLake vector store with OpenAI embeddings
    deep_lake = DeepLake(
        dataset_path=deeplake_path,
        read_only=True,
        embedding_function=embeddings,
    )
    # Initialize retriever and set search parameters
    retriever = deep_lake.as_retriever()
    retriever.search_kwargs.update({
        'distance_metric': 'cos',
        'fetch_k': 100,
        'maximal_marginal_relevance': True,
        'k': 10,
    })

    # List questions to answer in a row.
    # Initialize GPT model
    language_model= os.getenv('LANGUAGE_MODEL')
    model = ChatOpenAI(model_name=language_model, temperature=0.2) # gpt-3.5-turbo by default, edit in .env 
    qa = ConversationalRetrievalChain.from_llm(model, retriever=retriever)

    questions = [
        "What files are present in the chatgpt plugin quickstart repository?",
        "Can you summarize the chatgpt plugin quickstart repository readme file?",
        "Can you show me the ai-plugin.json?",
        "What dependencies are required from package.json?"
    ] 
    chat_history = []

    for question in questions:  
        result = qa({"question": question, "chat_history": chat_history})
        chat_history.append((question, result['answer']))
        print(f"-> **Question**: {question}\n")
        print(f"**Answer**: {result['answer']}\n")
"""

if __name__ == "__main__":
    main()
