"""
Evaluation metrics
Retrieval quality is measured with a recall@k metric.

Recall@k Calculation
For each question, recall@k is the share of its correct sources that you retrieve in your
top-k results. A correct source counts as found when one of your results is in the same
file and overlaps its character range.

The overlap bar is low (an IoU of 0.05), so you do not need to match the reference span
exactly: retrieving a chunk that covers the right region of the right file is enough. A
result in a different file never counts, which is why file_path must be exact.
The moulinette validates your output, then reports recall at several values of k. Docs must
reach 80 % recall@5, code 50 %.
"""