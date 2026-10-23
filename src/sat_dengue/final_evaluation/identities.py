"""Explicit engineering identities of the frozen Stage 5 input chain."""

PROPOSAL_SHA = "66d7208066476b027721182d185770d2522dfe5d891caf4b3b2759177dcc5e09"
FINAL = (
    "artifacts/model_final_evaluation/"
    "768406f872f4b859756b4603d684b965841e8c37a0f00c7f34618786dfa76e35"
)
STAGE5 = (
    "artifacts/model_evaluation/dcab7855d25e6982d9afb21cc4bf50831cb48095fa2d7181afe3b5661b910cfd"
)
ASSESSMENT = (
    "artifacts/model_assessment/0f26a4eb97ad37075f3fba2d8da0afd55cf3450db945e8f9cb86d7dccac2f257"
)
NATIVE = {
    FINAL: {
        "bytes": 9956,
        "sha256": "5a526fa996112c86b014c533260f234b94c7c31bbcf47fa465fd61480c9b768f",
    },
    STAGE5: {
        "bytes": 83489,
        "sha256": "d1d954cd4194f306e17746ae95382d4c1c301743488d87a4090d5e2bbfe3fd0b",
    },
    ASSESSMENT: {
        "bytes": 3667,
        "sha256": "6e0a55cea0ca993506893ffedb68ab870a10e2b08916613b7c2ffe0a780a0bcb",
    },
}
