# V6 GDN Upstream Mapping

## Source

- repository: `https://github.com/d-ailin/GDN`
- commit: `9853899da860682669a134e4af315d036aab4eca`
- license: MIT
- license blob: `956d782cc7291c801373a8d256135b497597e539`
- license SHA-256: `ffdad180c52921c5fb96b388ac08a4b5fa9e8eed6fd531969726219877a70b33`

The existing local checkout and Git objects were read only. No branch was
fetched and no network source was substituted.

| File | Git blob SHA | SHA-256 |
|---|---|---|
| `models/GDN.py` | `e967790769a5ea38dfbaed3e0e77b22cd0c5c896` | `eedcdc73d48e9f34c384b1a7ad875e37580f3177e023d59608a14bc56c60eb66` |
| `models/graph_layer.py` | `77d9db23df4bfde2db69500d3fda2fc9b378e3e3` | `0963e4091f9625e867dd90e7b402a277085f5c659a7d70c28880f3ae229b7f79` |
| `datasets/TimeDataset.py` | `8eb0b4c580b78fec0248069b2c6a81fbe3ce080c` | `b1b9f6d53080d275d96ea7157bf4ded92131a1b566410fa7a7eaf96cc5084904` |
| `train.py` | `934bd50ab2acffcb9d028633960f722eae3440de` | `885687aec4c42ac6a2b4782aced7ebf8785e0d0b56b787f39695a4f1b84169e1` |
| `test.py` | `58ae62520552cd0548318ed14d4a5fc07965a4f8` | `156de035bdb1b2d4931787cd863090064e2f4c6b05ae92e3f2103cba305eddeb` |
| `evaluate.py` | `ae4110dc37d3665a93c1a88de35d313da6b4dd73` | `daa647f55b26e1dd627257a25b9084c60fc36488f58c45faf9d7455491231e83` |
| `util/net_struct.py` | `ccc6256180aeb40395004a695446721fe073c754` | `e0079cc401b2b9cf6e03634146382581accf267918d91c1ebffe628c82a6bac4` |

## Feature Mapping

`models/GDN.py` and `models/graph_layer.py` establish the dynamic cosine graph,
custom embedding-conditioned attention, output gating, normalization, and
dropout behavior. `TimeDataset.py` establishes sliding-window inputs and
next-value targets. `train.py` establishes MSE optimization and validation-loss
checkpoint selection. `test.py` and `evaluate.py` establish prediction and
anomaly-score behavior but are not reused as v6 selection logic.
`util/net_struct.py` establishes upstream fully connected or dataset-specific
prior graph construction; the project CandidateUniverse is an intentional
replacement, not a faithful copy.
