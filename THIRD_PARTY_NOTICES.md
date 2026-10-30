# Third-party materials

- **ProsusAI/finbert**: use the [published model card](https://huggingface.co/ProsusAI/finbert).
  At retrieval on 29 October 2026 its weights are labelled CC BY-NC-SA 4.0.
  Model weights are downloaded separately and are not included in the release ZIP.
  Cite Dogu Araci (2019), *FinBERT: Financial Sentiment Analysis with Pre-trained
  Language Models*, [arXiv:1908.10063](https://arxiv.org/abs/1908.10063).
- **Loughran-McDonald dictionary**: obtained from the authors'
  [Notre Dame page](https://sraf.nd.edu/loughranmcdonald-master-dictionary/).
  Academic research is permitted under the terms on that page; commercial
  licensing is separate. The dictionary is excluded from the release ZIP.
- **NSE**: universe and nominal prices originate from public NSE feeds and
  dated NSE bhavcopies. `data/research/sources.json` records download URLs and
  raw-file hashes. Public availability does not transfer ownership of the data.
- **Google News / publishers**: the research corpus contains headline metadata
  and links, not full articles. Each record retains its publisher and URL.
  Search-result coverage is retrospective and incomplete. Publisher material
  remains subject to its original rights; the MIT code license does not cover it.

No external repository's code or dataset was copied into this project.
