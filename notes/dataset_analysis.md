# BGL Dataset Analysis

## Dataset

Dataset: BGL (Blue Gene/L supercomputer log)

Source: LogHub, Zenodo record 8196385, version v8.
BGL archive: `BGL.zip`
BGL archive MD5: `4452953c470f2d95fcb32d5f6e733f7a`
DOI: `10.5281/zenodo.8196385`

The BGL dataset is a labelled system log dataset from the Blue Gene/L
supercomputer. LogHub reports 4,747,963 log lines covering 214.7 days.

Source:
https://github.com/logpai/loghub

## Local Dataset Statistics

The downloaded BGL.log file was analyzed using `src/analyze_bgl.py`.
The script now also applies a lightweight in-repository implementation of the
published Drain fixed-depth log-template extraction approach to the unstructured
message portion of the records. Drain groups similar log lines into templates
before downstream log analysis; the implementation is intentionally limited to
this template-mining use case and is not a full log parser.

Results:

- Total records: 4,747,963
- Normal records: 4,399,503
- Alert records: 348,460
- Alert percentage: 7.34%
- Distinct labels: 42

In the BGL dataset, `-` is used as the normal/non-alert label.
The remaining labels represent alert categories.

## Top Alert Labels

| Alert label | Records |
|---|---:|
| KERNDTLB | 152,734 |
| KERNSTOR | 63,491 | 
| APPSEV | 49,651 |
| KERNMNTF | 31,531 |
| KERNTERM | 23,338 |
| KERNREC | 6,145 |
| APPREAD | 5,983 |
| KERNRTSP | 3,983 |
| APPRES | 2,370 |
| APPUNAV | 2,048 |
| APPTO | 1,991 |
| KERNMICRO | 1,503 |
| APPOUT | 816 |
| KERNMNT | 720 |
| APPBUSY | 512 |

## Initial Interpretation

The alert labels show several broad categories of infrastructure
problems, including kernel, storage/filesystem, application, and
communication-related failures.

The template miner is used to group structurally similar BGL messages and to
make the preprocessing step explicit and reproducible. The simulator does not
reproduce all 42 BGL labels. Instead, the real
BGL distribution will be used to inform a smaller set of incident types
and candidate remediation actions required by the Earned Autonomy
project.

This abstraction is a project simulation choice and is not a claim that
BGL directly defines these six remediation scenarios.

## Reproducibility

The raw BGL dataset is kept outside the Git repository in:

`C:\Users\KIIT0001\earnedauto-data\`

The analysis can be reproduced with:

```text
python src/analyze_bgl.py --template-sample 10000
```

## Template Extraction Method

The template extraction follows the core idea of Drain: messages are grouped by
length in a fixed-depth prefix tree, candidate templates are compared using
token-level similarity, and differing token positions are generalized to the
`<*>` wildcard. The repository contains a small deterministic implementation
(`src/log_templates.py`) so the project does not depend on a separate parser
service or a large parsing framework.

By default, the first 10,000 records are mined for templates. The complete BGL
label counts are still scanned over all records, so the incident-frequency
statistics remain based on the full dataset. The sample size can be changed with
`--template-sample`.
