#!/bin/bash

# Uninstall the deprecated plugins
pip uninstall -y pinecone-plugin-inference pinecone-plugin-interface

# Install the specific version of Pinecone
pip install pinecone==6.0.0
