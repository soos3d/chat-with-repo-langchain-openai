import os
from dotenv import load_dotenv
from langchain.vectorstores import DeepLake
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.embeddings import OpenAIEmbeddings
from langchain.callbacks import get_openai_callback

# Load environment variables from .env file
load_dotenv()

# Set environment variables
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
os.environ['ACTIVELOOP_TOKEN'] = os.getenv('ACTIVELOOP_TOKEN')
language_model = os.getenv('LANGUAGE_MODEL')

# Set DeepLake dataset path
DEEPLAKE_PATH = os.getenv('DATASET_PATH')

# Initialize OpenAI embeddings and disallow special tokens
EMBEDDINGS = OpenAIEmbeddings(disallowed_special=())

# Initialize DeepLake vector store with OpenAI embeddings
deep_lake = DeepLake(
    dataset_path=DEEPLAKE_PATH,
    read_only=True,
    embedding_function=EMBEDDINGS,
)

# Initialize retriever and set search parameters
retriever = deep_lake.as_retriever()
retriever.search_kwargs.update({
    'distance_metric': 'cos',
    'fetch_k': 100,
    'maximal_marginal_relevance': True,
    'k': 10,
})

# Initialize ChatOpenAI model
model = ChatOpenAI(model_name=language_model, temperature=0.2) # gpt-3.5-turbo by default. Use gpt-4 for better and more accurate responses 

# Initialize ConversationalRetrievalChain
qa = ConversationalRetrievalChain.from_llm(model, retriever=retriever)

# Initialize chat history
chat_history = []

def get_user_input():
    """Get user input and handle 'quit' command."""
    question = input("\nPlease enter your question (or 'quit' to stop): ")
    if question.lower() == 'quit':
        return None
    return question

def print_answer(question, answer):
    """Format and print question and answer."""
    print(f"\nQuestion: {question}\nAnswer: {answer}\n")

def main():
    """Main program loop."""
    while True:
        question = get_user_input()
        if question is None:  # User has quit
            break

        # Display token usage and approximate costs
        with get_openai_callback() as tokens_usage:
            result = qa({"question": question, "chat_history": chat_history})
            chat_history.append((question, result['answer']))
            print_answer(question, result['answer'])
            print(tokens_usage)

if __name__ == "__main__":
    main()
