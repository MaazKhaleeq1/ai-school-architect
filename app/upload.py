import os
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_community.document_loaders.pdf import PyPDFLoader
from app.github_repo import GitHubRepo
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_community.document_loaders import DirectoryLoader

ghr = GitHubRepo('https://github.com/trilogy-group/Lithium-FAF-Copilot/')
files = ghr.get_file_structure()
print(files)

for file in files:
    # Split documents into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
    documents = text_splitter.split_text(ghr.get_file_content(file))

    # Choose the embedding model and vector store 
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")  # Adjust model name if needed
    PineconeVectorStore.from_texts(texts=documents, embedding=embeddings, index_name="lithium-faf-code")

print("Loading to vectorstore done")