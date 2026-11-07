"""
Chunking. Duas estratégias, uma para .py e outra para .md/texto. 
O que mais importa aqui:
Cada chunk guarda o file_path exato (data/raw/vllm-0.10.1/...) 
e os índices de caracteres no ficheiro original. 
Se limpares ou alterares o texto, os índices deixam de bater certo.
Nunca passar o max_chunk_size.
Nos .py, cortar por funções e classes. Nos .md, cortar por headings e parágrafos. Se um bloco for grande demais, partes esse bloco.
Indexer. O BM25 é o mais simples de pôr a dar bons resultados. Corre sobre os chunks e guarda o índice em data/processed/. Atenção ao limite de 5 minutos para indexar tudo.
Searcher, com os comandos search e search_dataset. Com o Fire já montado no __main__.py.
evaluate. Faz isto antes do answer generator. Os 80% de recall nas perguntas de docs e 50% nas de código é que decidem a nota. Precisas de medir cedo para afinar o chunking e a tokenização, por exemplo partir snake_case e CamelCase em palavras.
Answer generator. Fica para o fim. É o que conta menos para a avaliação e o mais lento de testar.
"""
