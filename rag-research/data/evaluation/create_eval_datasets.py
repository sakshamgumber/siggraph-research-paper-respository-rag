import json
from pathlib import Path

# Paths
eval_dir = Path("data/evaluation")
eval_dir.mkdir(parents=True, exist_ok=True)

pdf_catalog = {
    "PDF-1": {
        "pdf_number": "PDF-1",
        "pdf_filename": "3528233.3530716.pdf",
        "paper_id": "3528233.3530716",
        "title": "Low-poly Mesh Generation for Building Models",
    },
    "PDF-2": {
        "pdf_number": "PDF-2",
        "pdf_filename": "3528233.3530720.pdf",
        "paper_id": "3528233.3530720",
        "title": "Animating Portrait Line Drawings from a Single Face Photo and a Speech Signal",
    },
    "PDF-3": {
        "pdf_number": "PDF-3",
        "pdf_filename": "3528233.3530729.pdf",
        "paper_id": "3528233.3530729",
        "title": "Comparison of single image HDR reconstruction methods — the caveats of quality assessment",
    },
    "PDF-4": {
        "pdf_number": "PDF-4",
        "pdf_filename": "3528233.3530732.pdf",
        "paper_id": "3528233.3530732",
        "title": "Neural Layered BRDFs",
    },
    "PDF-5": {
        "pdf_number": "PDF-5",
        "pdf_filename": "3528233.3530740.pdf",
        "paper_id": "3528233.3530740",
        "title": "Drivable Volumetric Avatars using Texel-Aligned Features",
    },
    "PDF-6": {
        "pdf_number": "PDF-6",
        "pdf_filename": "3528233.3530753.pdf",
        "paper_id": "3528233.3530753",
        "title": "MoRF: Morphable Radiance Fields for Multiview Neural Head Modeling",
    },
}

questions_data = [
    {
        "id": "rag_001",
        "question_number": 1,
        "category": "Exact Fact",
        "type": "exact_fact",
        "difficulty": "easy",
        "question": "How many building models were used to evaluate the low-poly mesh generation method?",
        "expected_answer": "The evaluation dataset contains 100 building models with varying styles.",
        "pdf_number": "PDF-1",
        "pdf_filename": "3528233.3530716.pdf",
        "paper_id": "3528233.3530716",
        "source": {
            "pdf_number": "PDF-1",
            "pdf": "3528233.3530716.pdf",
            "title": "Low-poly Mesh Generation for Building Models",
            "lines": "117–125"
        },
        "expected_retrieval": ["100 building models"],
        "gold_chunk_ids": ["3528233.3530716_chunk_002", "3528233.3530716_chunk_048"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_002",
        "question_number": 2,
        "category": "Exact Fact",
        "type": "exact_fact",
        "difficulty": "easy",
        "question": "What are the three stages of the proposed low-poly mesh generation algorithm?",
        "expected_answer": "1. Generate a watertight visual hull using Boolean intersection of 3D extrusions of input silhouettes. 2. Carve redundant structures from the visual hull using Boolean subtraction. 3. Progressively simplify the carved mesh and extract a Pareto front.",
        "pdf_number": "PDF-1",
        "pdf_filename": "3528233.3530716.pdf",
        "paper_id": "3528233.3530716",
        "source": {
            "pdf_number": "PDF-1",
            "pdf": "3528233.3530716.pdf",
            "title": "Low-poly Mesh Generation for Building Models",
            "lines": "25–33"
        },
        "expected_retrieval": ["visual hull", "Boolean subtraction", "carving", "simplification", "Pareto front"],
        "gold_chunk_ids": ["3528233.3530716_chunk_002", "3528233.3530716_chunk_009"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_003",
        "question_number": 3,
        "category": "Exact Fact",
        "type": "exact_fact",
        "difficulty": "easy",
        "question": "What two temporal coherence losses are proposed for portrait line-drawing animation?",
        "expected_answer": "The paper proposes: (1) a temporal coherence loss based on warping, and (2) a temporal coherence loss based on a temporal coherence discriminator.",
        "pdf_number": "PDF-2",
        "pdf_filename": "3528233.3530720.pdf",
        "paper_id": "3528233.3530720",
        "source": {
            "pdf_number": "PDF-2",
            "pdf": "3528233.3530720.pdf",
            "title": "Animating Portrait Line Drawings from a Single Face Photo and a Speech Signal",
            "lines": "47–51"
        },
        "expected_retrieval": ["temporal coherence loss based on warping", "temporal coherence loss based on a temporal coherence discriminator"],
        "gold_chunk_ids": ["3528233.3530720_chunk_009", "3528233.3530720_chunk_010", "3528233.3530720_chunk_032"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_004",
        "question_number": 4,
        "category": "Exact Fact",
        "type": "exact_fact",
        "difficulty": "easy",
        "question": "What three metrics are used for quantitative evaluation of the portrait animation method?",
        "expected_answer": "1. FID for individual-frame quality and similarity between generated and real distributions. 2. Inter-frame SSIM for temporal/inter-frame coherence. 3. Lip Landmark Distance (LMD) for lip synchronization.",
        "pdf_number": "PDF-2",
        "pdf_filename": "3528233.3530720.pdf",
        "paper_id": "3528233.3530720",
        "source": {
            "pdf_number": "PDF-2",
            "pdf": "3528233.3530720.pdf",
            "title": "Animating Portrait Line Drawings from a Single Face Photo and a Speech Signal",
            "lines": "689–693"
        },
        "expected_retrieval": ["FID", "Inter-frame SSIM", "Lip Landmark Distance", "LMD"],
        "gold_chunk_ids": ["3528233.3530720_chunk_036", "3528233.3530720_chunk_045"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_005",
        "question_number": 5,
        "category": "Exact Fact",
        "type": "exact_fact",
        "difficulty": "easy",
        "question": "How many video clips were used for the quantitative evaluation of the portrait animation method?",
        "expected_answer": "The authors evaluated the methods on 118 video clips from the VoxCeleb2 dataset.",
        "pdf_number": "PDF-2",
        "pdf_filename": "3528233.3530720.pdf",
        "paper_id": "3528233.3530720",
        "source": {
            "pdf_number": "PDF-2",
            "pdf": "3528233.3530720.pdf",
            "title": "Animating Portrait Line Drawings from a Single Face Photo and a Speech Signal",
            "lines": "689–693"
        },
        "expected_retrieval": ["118 video clips", "VoxCeleb2"],
        "gold_chunk_ids": ["3528233.3530720_chunk_040", "3528233.3530720_chunk_045"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_006",
        "question_number": 6,
        "category": "Exact Fact",
        "type": "exact_fact",
        "difficulty": "easy",
        "question": "What FID score does the proposed portrait animation method achieve?",
        "expected_answer": "The proposed method, Ours, achieves an FID of 135.2.",
        "pdf_number": "PDF-2",
        "pdf_filename": "3528233.3530720.pdf",
        "paper_id": "3528233.3530720",
        "source": {
            "pdf_number": "PDF-2",
            "pdf": "3528233.3530720.pdf",
            "title": "Animating Portrait Line Drawings from a Single Face Photo and a Speech Signal",
            "lines": "595–600"
        },
        "expected_retrieval": ["FID of 135.2", "135.2"],
        "gold_chunk_ids": ["3528233.3530720_chunk_036", "3528233.3530720_chunk_037"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_007",
        "question_number": 7,
        "category": "Exact Fact",
        "type": "exact_fact",
        "difficulty": "easy",
        "question": "How many subjects was MoRF trained on according to the paper's stated limitation?",
        "expected_answer": "MoRF was trained on 15 subjects.",
        "pdf_number": "PDF-6",
        "pdf_filename": "3528233.3530753.pdf",
        "paper_id": "3528233.3530753",
        "source": {
            "pdf_number": "PDF-6",
            "pdf": "3528233.3530753.pdf",
            "title": "MoRF: Morphable Radiance Fields for Multiview Neural Head Modeling",
            "lines": "639–647"
        },
        "expected_retrieval": ["15 subjects"],
        "gold_chunk_ids": ["3528233.3530753_chunk_048"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_008",
        "question_number": 8,
        "category": "Exact Fact",
        "type": "exact_fact",
        "difficulty": "easy",
        "question": "What does each identity receive in MoRF's shared volumetric model?",
        "expected_answer": "Each identity is represented by a latent code.",
        "pdf_number": "PDF-6",
        "pdf_filename": "3528233.3530753.pdf",
        "paper_id": "3528233.3530753",
        "source": {
            "pdf_number": "PDF-6",
            "pdf": "3528233.3530753.pdf",
            "title": "MoRF: Morphable Radiance Fields for Multiview Neural Head Modeling",
            "lines": "107–115"
        },
        "expected_retrieval": ["latent code", "represented by a latent code"],
        "gold_chunk_ids": ["3528233.3530753_chunk_010", "3528233.3530753_chunk_026", "3528233.3530753_chunk_037"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_009",
        "question_number": 9,
        "category": "Semantic / Paraphrase",
        "type": "semantic",
        "difficulty": "medium",
        "question": "How does the building-model system automatically transform a detailed 3D building into a simpler model without losing too much of its appearance?",
        "expected_answer": "It constructs a visual hull from input silhouettes, removes redundant volumes to recover important concave structures, and then progressively simplifies the resulting mesh while optimizing the trade-off between triangle count and visual similarity.",
        "pdf_number": "PDF-1",
        "pdf_filename": "3528233.3530716.pdf",
        "paper_id": "3528233.3530716",
        "source": {
            "pdf_number": "PDF-1",
            "pdf": "3528233.3530716.pdf",
            "title": "Low-poly Mesh Generation for Building Models",
            "lines": "97–118"
        },
        "expected_retrieval": ["visual hull", "concave structures", "progressively simplifies", "visual similarity"],
        "gold_chunk_ids": ["3528233.3530716_chunk_002", "3528233.3530716_chunk_009", "3528233.3530716_chunk_010", "3528233.3530716_chunk_038"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_010",
        "question_number": 10,
        "category": "Semantic / Paraphrase",
        "type": "semantic",
        "difficulty": "medium",
        "question": "Why can simply applying a photo-to-drawing conversion independently to every video frame produce bad animation?",
        "expected_answer": "Because independently processing frames can cause severe inter-frame discontinuities. For sparse portrait drawings, appearing and disappearing line elements make these inconsistencies especially noticeable.",
        "pdf_number": "PDF-2",
        "pdf_filename": "3528233.3530720.pdf",
        "paper_id": "3528233.3530720",
        "source": {
            "pdf_number": "PDF-2",
            "pdf": "3528233.3530720.pdf",
            "title": "Animating Portrait Line Drawings from a Single Face Photo and a Speech Signal",
            "lines": "84–95"
        },
        "expected_retrieval": ["inter-frame discontinuities", "sparse line elements", "appearance and disappearance"],
        "gold_chunk_ids": ["3528233.3530720_chunk_007"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_011",
        "question_number": 11,
        "category": "Semantic / Paraphrase",
        "type": "semantic",
        "difficulty": "medium",
        "question": "How does the BRDF method avoid repeatedly performing expensive physical light-transport simulations?",
        "expected_answer": "It represents BRDFs in a latent space and performs the layering operation on latent vectors using a neural layering network, replacing the expensive random-walk computation.",
        "pdf_number": "PDF-4",
        "pdf_filename": "3528233.3530732.pdf",
        "paper_id": "3528233.3530732",
        "source": {
            "pdf_number": "PDF-4",
            "pdf": "3528233.3530732.pdf",
            "title": "Neural Layered BRDFs",
            "lines": "102–106"
        },
        "expected_retrieval": ["latent space", "neural layering network", "random-walk computation"],
        "gold_chunk_ids": ["3528233.3530732_chunk_004", "3528233.3530732_chunk_009", "3528233.3530732_chunk_013"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_012",
        "question_number": 12,
        "category": "Semantic / Paraphrase",
        "type": "semantic",
        "difficulty": "medium",
        "question": "Why do traditional NeRF-based face models have difficulty supporting multiple identities?",
        "expected_answer": "Traditional NeRFs are generally designed to represent a single scene/identity. MoRF addresses this by using a single volumetric model capable of representing multiple identities, with each identity represented through a latent code.",
        "pdf_number": "PDF-6",
        "pdf_filename": "3528233.3530753.pdf",
        "paper_id": "3528233.3530753",
        "source": {
            "pdf_number": "PDF-6",
            "pdf": "3528233.3530753.pdf",
            "title": "MoRF: Morphable Radiance Fields for Multiview Neural Head Modeling",
            "lines": "93–112"
        },
        "expected_retrieval": ["single scene", "multiple identities", "latent code", "single volumetric model"],
        "gold_chunk_ids": ["3528233.3530753_chunk_010", "3528233.3530753_chunk_019"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_013",
        "question_number": 13,
        "category": "Semantic / Paraphrase",
        "type": "semantic",
        "difficulty": "medium",
        "question": "Why can conventional objective metrics be unreliable when judging single-image HDR reconstruction?",
        "expected_answer": "Tone and color differences caused by inaccurate camera-response-curve inversion can dominate the metric scores, even though these differences may not correspond well to human judgments of image quality.",
        "pdf_number": "PDF-3",
        "pdf_filename": "3528233.3530729.pdf",
        "paper_id": "3528233.3530729",
        "source": {
            "pdf_number": "PDF-3",
            "pdf": "3528233.3530729.pdf",
            "title": "Comparison of single image HDR reconstruction methods — the caveats of quality assessment",
            "lines": "112–130"
        },
        "expected_retrieval": ["camera-response-curve inversion", "CRF reconstruction", "metric scores", "subjective results"],
        "gold_chunk_ids": ["3528233.3530729_chunk_002", "3528233.3530729_chunk_008", "3528233.3530729_chunk_040"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_014",
        "question_number": 14,
        "category": "Multi-Hop Retrieval",
        "type": "multi_hop",
        "difficulty": "hard",
        "question": "Why does the visual hull alone fail to fully represent some buildings, and how does the proposed method fix this?",
        "expected_answer": "The visual hull captures the input silhouette but can miss important concave features. The second stage therefore subtracts redundant volumes from the visual hull to create a carved mesh that recovers those concave features.",
        "pdf_number": "PDF-1",
        "pdf_filename": "3528233.3530716.pdf",
        "paper_id": "3528233.3530716",
        "sources": [
            {
                "pdf_number": "PDF-1",
                "pdf": "3528233.3530716.pdf",
                "title": "Low-poly Mesh Generation for Building Models",
                "lines": "97–109"
            },
            {
                "pdf_number": "PDF-1",
                "pdf": "3528233.3530716.pdf",
                "title": "Low-poly Mesh Generation for Building Models",
                "lines": "105–112"
            }
        ],
        "required_concepts": ["visual hull", "concave features", "carved mesh", "Boolean subtraction"],
        "gold_chunk_ids": ["3528233.3530716_chunk_002", "3528233.3530716_chunk_009", "3528233.3530716_chunk_017", "3528233.3530716_chunk_032"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_015",
        "question_number": 15,
        "category": "Multi-Hop Retrieval",
        "type": "multi_hop",
        "difficulty": "hard",
        "question": "Describe the pipeline that converts speech into an animated portrait line drawing.",
        "expected_answer": "The system first uses speech to predict facial landmark movements. Those target landmarks are then used by a GAN that simultaneously performs photo-to-drawing domain transfer and facial-geometry changes. Temporal coherence losses are subsequently used to make the animation consistent across frames.",
        "pdf_number": "PDF-2",
        "pdf_filename": "3528233.3530720.pdf",
        "paper_id": "3528233.3530720",
        "sources": [
            {
                "pdf_number": "PDF-2",
                "pdf": "3528233.3530720.pdf",
                "title": "Animating Portrait Line Drawings from a Single Face Photo and a Speech Signal",
                "lines": "236–247"
            },
            {
                "pdf_number": "PDF-2",
                "pdf": "3528233.3530720.pdf",
                "title": "Animating Portrait Line Drawings from a Single Face Photo and a Speech Signal",
                "lines": "47–51"
            }
        ],
        "required_concepts": ["speech to predict facial landmark movements", "GAN domain transfer", "facial-geometry changes", "temporal coherence losses"],
        "gold_chunk_ids": ["3528233.3530720_chunk_009", "3528233.3530720_chunk_010", "3528233.3530720_chunk_019"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_016",
        "question_number": 16,
        "category": "Multi-Hop Retrieval",
        "type": "multi_hop",
        "difficulty": "hard",
        "question": "How does MoRF represent multiple human identities while maintaining a common 3D representation?",
        "expected_answer": "MoRF trains a single volumetric model for all identities. Each identity has a latent code, while subject-specific deformation fields align identities to a common canonical NeRF. Skin regions receive partial deformation supervision because correspondence information is available there.",
        "pdf_number": "PDF-6",
        "pdf_filename": "3528233.3530753.pdf",
        "paper_id": "3528233.3530753",
        "sources": [
            {
                "pdf_number": "PDF-6",
                "pdf": "3528233.3530753.pdf",
                "title": "MoRF: Morphable Radiance Fields for Multiview Neural Head Modeling",
                "lines": "107–118"
            }
        ],
        "required_concepts": ["single volumetric model", "latent code", "subject-specific deformation fields", "canonical NeRF", "skin region supervision"],
        "gold_chunk_ids": ["3528233.3530753_chunk_010", "3528233.3530753_chunk_025", "3528233.3530753_chunk_028", "3528233.3530753_chunk_031"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_017",
        "question_number": 17,
        "category": "Multi-Hop Retrieval",
        "type": "multi_hop",
        "difficulty": "hard",
        "question": "Why does the avatar method use both texel-aligned features and a volumetric representation?",
        "expected_answer": "Texel-aligned features provide a localized, dense conditioning signal that combines structural information from a skeleton-based model with observed image signals. The volumetric representation handles articulated human bodies and avoids requiring high-quality mesh tracking.",
        "pdf_number": "PDF-5",
        "pdf_filename": "3528233.3530740.pdf",
        "paper_id": "3528233.3530740",
        "sources": [
            {
                "pdf_number": "PDF-5",
                "pdf": "3528233.3530740.pdf",
                "title": "Drivable Volumetric Avatars using Texel-Aligned Features",
                "lines": "64–79"
            }
        ],
        "required_concepts": ["texel-aligned features", "dense conditioning signal", "volumetric representation", "no high-quality mesh tracking"],
        "gold_chunk_ids": ["3528233.3530740_chunk_003", "3528233.3530740_chunk_010", "3528233.3530740_chunk_014"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_018",
        "question_number": 18,
        "category": "Keyword-Mismatch Tests",
        "type": "keyword_mismatch",
        "difficulty": "medium",
        "question": "How does the method remove unnecessary geometric parts from the initial building representation?",
        "expected_answer": "It uses Boolean subtraction of 3D primitives to carve redundant volumes from the visual hull.",
        "pdf_number": "PDF-1",
        "pdf_filename": "3528233.3530716.pdf",
        "paper_id": "3528233.3530716",
        "source": {
            "pdf_number": "PDF-1",
            "pdf": "3528233.3530716.pdf",
            "title": "Low-poly Mesh Generation for Building Models",
            "lines": "25–33"
        },
        "keyword_mismatch_rationale": "Query says 'remove unnecessary geometric parts'; paper says 'carve redundant structures / Boolean subtraction'.",
        "expected_retrieval": ["carve redundant structures", "Boolean subtraction", "visual hull"],
        "gold_chunk_ids": ["3528233.3530716_chunk_002", "3528233.3530716_chunk_009", "3528233.3530716_chunk_032"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_019",
        "question_number": 19,
        "category": "Keyword-Mismatch Tests",
        "type": "keyword_mismatch",
        "difficulty": "medium",
        "question": "How does the portrait-animation system prevent individual frames from looking inconsistent with their neighbors?",
        "expected_answer": "It introduces two temporal coherence losses: one based on warping and another based on a temporal coherence discriminator.",
        "pdf_number": "PDF-2",
        "pdf_filename": "3528233.3530720.pdf",
        "paper_id": "3528233.3530720",
        "source": {
            "pdf_number": "PDF-2",
            "pdf": "3528233.3530720.pdf",
            "title": "Animating Portrait Line Drawings from a Single Face Photo and a Speech Signal",
            "lines": "47–51"
        },
        "keyword_mismatch_rationale": "Query says 'prevent individual frames from looking inconsistent with their neighbors'; paper says 'temporal coherence losses'.",
        "expected_retrieval": ["temporal coherence losses", "warping", "temporal coherence discriminator"],
        "gold_chunk_ids": ["3528233.3530720_chunk_009", "3528233.3530720_chunk_010", "3528233.3530720_chunk_032"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_020",
        "question_number": 20,
        "category": "Keyword-Mismatch Tests",
        "type": "keyword_mismatch",
        "difficulty": "medium",
        "question": "How does the HDR evaluation process compensate for errors introduced when recovering the camera response?",
        "expected_answer": "It introduces an explicit CRF correction step before computing image-quality metrics.",
        "pdf_number": "PDF-3",
        "pdf_filename": "3528233.3530729.pdf",
        "paper_id": "3528233.3530729",
        "source": {
            "pdf_number": "PDF-3",
            "pdf": "3528233.3530729.pdf",
            "title": "Comparison of single image HDR reconstruction methods — the caveats of quality assessment",
            "lines": "119–130"
        },
        "keyword_mismatch_rationale": "Query says 'compensate for errors introduced when recovering the camera response'; paper says 'CRF correction step'.",
        "expected_retrieval": ["CRF correction", "camera response curve", "image quality metrics"],
        "gold_chunk_ids": ["3528233.3530729_chunk_002", "3528233.3530729_chunk_008", "3528233.3530729_chunk_040"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_021",
        "question_number": 21,
        "category": "Keyword-Mismatch Tests",
        "type": "keyword_mismatch",
        "difficulty": "medium",
        "question": "How does the neural material model combine multiple material layers efficiently?",
        "expected_answer": "It converts BRDFs into latent representations and performs layering operations directly on the latent vectors using a neural layering network.",
        "pdf_number": "PDF-4",
        "pdf_filename": "3528233.3530732.pdf",
        "paper_id": "3528233.3530732",
        "source": {
            "pdf_number": "PDF-4",
            "pdf": "3528233.3530732.pdf",
            "title": "Neural Layered BRDFs",
            "lines": "102–106"
        },
        "keyword_mismatch_rationale": "Query says 'combine multiple material layers efficiently'; paper says 'layering operations directly on the latent vectors using a neural layering network'.",
        "expected_retrieval": ["latent representations", "neural layering network", "latent vectors"],
        "gold_chunk_ids": ["3528233.3530732_chunk_004", "3528233.3530732_chunk_009", "3528233.3530732_chunk_013"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_022",
        "question_number": 22,
        "category": "Keyword-Mismatch Tests",
        "type": "keyword_mismatch",
        "difficulty": "medium",
        "question": "How does the avatar method preserve detailed information from the driving performer instead of compressing everything into body pose?",
        "expected_answer": "It uses texel-aligned features, a localized representation that combines structural priors from a skeleton-based model with observed sparse image signals.",
        "pdf_number": "PDF-5",
        "pdf_filename": "3528233.3530740.pdf",
        "paper_id": "3528233.3530740",
        "source": {
            "pdf_number": "PDF-5",
            "pdf": "3528233.3530740.pdf",
            "title": "Drivable Volumetric Avatars using Texel-Aligned Features",
            "lines": "64–72"
        },
        "keyword_mismatch_rationale": "Query says 'preserve detailed information from the driving performer instead of compressing everything into body pose'; paper says 'texel-aligned features'.",
        "expected_retrieval": ["texel-aligned features", "localized representation", "dense conditioning signal"],
        "gold_chunk_ids": ["3528233.3530740_chunk_003", "3528233.3530740_chunk_010", "3528233.3530740_chunk_030"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_023",
        "question_number": 23,
        "category": "Numerical Retrieval",
        "type": "numerical",
        "difficulty": "medium",
        "question": "What is the largest element count that users can tolerate during the low-poly mesh simplification process?",
        "expected_answer": "The paper denotes this threshold as T, the largest element count users are willing to tolerate.",
        "pdf_number": "PDF-1",
        "pdf_filename": "3528233.3530716.pdf",
        "paper_id": "3528233.3530716",
        "source": {
            "pdf_number": "PDF-1",
            "pdf": "3528233.3530716.pdf",
            "title": "Low-poly Mesh Generation for Building Models",
            "lines": "514–522"
        },
        "expected_retrieval": ["largest element count users can tolerate", "threshold as T", "T"],
        "gold_chunk_ids": ["3528233.3530716_chunk_038"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_024",
        "question_number": 24,
        "category": "Numerical Retrieval",
        "type": "numerical",
        "difficulty": "easy",
        "question": "What FID value does the proposed portrait-animation method report?",
        "expected_answer": "135.2",
        "pdf_number": "PDF-2",
        "pdf_filename": "3528233.3530720.pdf",
        "paper_id": "3528233.3530720",
        "source": {
            "pdf_number": "PDF-2",
            "pdf": "3528233.3530720.pdf",
            "title": "Animating Portrait Line Drawings from a Single Face Photo and a Speech Signal",
            "lines": "595–600"
        },
        "expected_retrieval": ["135.2"],
        "gold_chunk_ids": ["3528233.3530720_chunk_036", "3528233.3530720_chunk_037"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_025",
        "question_number": 25,
        "category": "Numerical Retrieval",
        "type": "numerical",
        "difficulty": "easy",
        "question": "How many VoxCeleb2 video clips were used for quantitative evaluation?",
        "expected_answer": "118 video clips.",
        "pdf_number": "PDF-2",
        "pdf_filename": "3528233.3530720.pdf",
        "paper_id": "3528233.3530720",
        "source": {
            "pdf_number": "PDF-2",
            "pdf": "3528233.3530720.pdf",
            "title": "Animating Portrait Line Drawings from a Single Face Photo and a Speech Signal",
            "lines": "689–693"
        },
        "expected_retrieval": ["118 video clips", "VoxCeleb2"],
        "gold_chunk_ids": ["3528233.3530720_chunk_040", "3528233.3530720_chunk_045"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_026",
        "question_number": 26,
        "category": "Numerical Retrieval",
        "type": "numerical",
        "difficulty": "easy",
        "question": "How many subjects was MoRF trained on?",
        "expected_answer": "15 subjects.",
        "pdf_number": "PDF-6",
        "pdf_filename": "3528233.3530753.pdf",
        "paper_id": "3528233.3530753",
        "source": {
            "pdf_number": "PDF-6",
            "pdf": "3528233.3530753.pdf",
            "title": "MoRF: Morphable Radiance Fields for Multiview Neural Head Modeling",
            "lines": "639–647"
        },
        "expected_retrieval": ["15 subjects"],
        "gold_chunk_ids": ["3528233.3530753_chunk_048"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_027",
        "question_number": 27,
        "category": "Long-Context Retrieval",
        "type": "long_context",
        "difficulty": "hard",
        "question": "What criterion causes an edge-flip operation in the low-poly mesh method?",
        "expected_answer": "An edge-flip is performed when a pair of adjacent triangles has an obtuse dihedral angle larger than the specified threshold, or when the exterior dihedral angle is below its corresponding threshold.",
        "pdf_number": "PDF-1",
        "pdf_filename": "3528233.3530716.pdf",
        "paper_id": "3528233.3530716",
        "source": {
            "pdf_number": "PDF-1",
            "pdf": "3528233.3530716.pdf",
            "title": "Low-poly Mesh Generation for Building Models",
            "lines": "569–580"
        },
        "expected_retrieval": ["edge-flip", "obtuse dihedral angle", "exterior dihedral angle"],
        "gold_chunk_ids": ["3528233.3530716_chunk_042"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_028",
        "question_number": 28,
        "category": "Long-Context Retrieval",
        "type": "long_context",
        "difficulty": "medium",
        "question": "What metrics are used to rank the simplified meshes in the Pareto set?",
        "expected_answer": "The meshes are ranked using: 1. Number of faces/triangles, 2. Visual difference from the input.",
        "pdf_number": "PDF-1",
        "pdf_filename": "3528233.3530716.pdf",
        "paper_id": "3528233.3530716",
        "source": {
            "pdf_number": "PDF-1",
            "pdf": "3528233.3530716.pdf",
            "title": "Low-poly Mesh Generation for Building Models",
            "lines": "513–522"
        },
        "expected_retrieval": ["Pareto", "number of faces", "visual differences"],
        "gold_chunk_ids": ["3528233.3530716_chunk_038"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_029",
        "question_number": 29,
        "category": "Long-Context Retrieval",
        "type": "long_context",
        "difficulty": "hard",
        "question": "How is the deformation field in MoRF supervised differently for skin and non-skin regions?",
        "expected_answer": "Skin regions can receive partial supervision because corresponding skin surfaces are available across identities. Non-skin areas such as hair lack those correspondences, so the deformation is learned automatically.",
        "pdf_number": "PDF-6",
        "pdf_filename": "3528233.3530753.pdf",
        "paper_id": "3528233.3530753",
        "source": {
            "pdf_number": "PDF-6",
            "pdf": "3528233.3530753.pdf",
            "title": "MoRF: Morphable Radiance Fields for Multiview Neural Head Modeling",
            "lines": "107–115"
        },
        "expected_retrieval": ["deformation field", "skin regions", "correspondence", "non-skin"],
        "gold_chunk_ids": ["3528233.3530753_chunk_024", "3528233.3530753_chunk_030", "3528233.3530753_chunk_032"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_030",
        "question_number": 30,
        "category": "Long-Context Retrieval",
        "type": "long_context",
        "difficulty": "hard",
        "question": "What does CRF correction change about the correlation between image-quality metrics and subjective results?",
        "expected_answer": "The paper reports that CRF correction substantially improves metric behavior. For example, the highest correlation increased from 0.47 before correction to 0.55 after correction in one analysis, although the authors note that this remained too low for meaningful prediction.",
        "pdf_number": "PDF-3",
        "pdf_filename": "3528233.3530729.pdf",
        "paper_id": "3528233.3530729",
        "source": {
            "pdf_number": "PDF-3",
            "pdf": "3528233.3530729.pdf",
            "title": "Comparison of single image HDR reconstruction methods — the caveats of quality assessment",
            "lines": "861–872"
        },
        "expected_retrieval": ["CRF correction", "0.47", "0.55", "correlation"],
        "gold_chunk_ids": ["3528233.3530729_chunk_036"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_031",
        "question_number": 31,
        "category": "Ambiguous Retrieval",
        "type": "ambiguous",
        "difficulty": "hard",
        "question": 'What is the "latent code" used for?',
        "expected_answer": "This question is intentionally ambiguous across multiple papers: For MoRF (PDF-6), a latent code represents an identity within the shared volumetric model. For Neural Layered BRDFs (PDF-4), latent vectors represent BRDFs and are used for layering operations.",
        "pdf_number": ["PDF-4", "PDF-6"],
        "pdf_filename": ["3528233.3530732.pdf", "3528233.3530753.pdf"],
        "paper_id": ["3528233.3530732", "3528233.3530753"],
        "sources": [
            {
                "pdf_number": "PDF-6",
                "pdf": "3528233.3530753.pdf",
                "title": "MoRF: Morphable Radiance Fields for Multiview Neural Head Modeling"
            },
            {
                "pdf_number": "PDF-4",
                "pdf": "3528233.3530732.pdf",
                "title": "Neural Layered BRDFs"
            }
        ],
        "expected_rag_behavior": "System should ask for clarification or explain both interpretations (MoRF identity latent code vs Neural Layered BRDFs material latent code) rather than blindly selecting one.",
        "expected_retrieval": ["latent code", "latent vectors", "identity", "BRDF"],
        "gold_chunk_ids": ["3528233.3530732_chunk_004", "3528233.3530732_chunk_016", "3528233.3530753_chunk_010", "3528233.3530753_chunk_026"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_032",
        "question_number": 32,
        "category": "Ambiguous Retrieval",
        "type": "ambiguous",
        "difficulty": "medium",
        "question": 'What does "warping" do in the proposed system?',
        "expected_answer": "In the portrait-animation paper (PDF-2), warping is part of the temporal coherence mechanism and the animation framework.",
        "pdf_number": "PDF-2",
        "pdf_filename": "3528233.3530720.pdf",
        "paper_id": "3528233.3530720",
        "source": {
            "pdf_number": "PDF-2",
            "pdf": "3528233.3530720.pdf",
            "title": "Animating Portrait Line Drawings from a Single Face Photo and a Speech Signal"
        },
        "expected_rag_behavior": "Identify the paper/context before answering.",
        "expected_retrieval": ["feature warping", "warping", "temporal coherence"],
        "gold_chunk_ids": ["3528233.3530720_chunk_009", "3528233.3530720_chunk_010", "3528233.3530720_chunk_025"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_033",
        "question_number": 33,
        "category": "Ambiguous Retrieval",
        "type": "ambiguous",
        "difficulty": "medium",
        "question": 'What is the "layering network"?',
        "expected_answer": "In Neural Layered BRDFs, it is the neural network that performs layering operations on latent BRDF vectors, replacing expensive random-walk simulation.",
        "pdf_number": "PDF-4",
        "pdf_filename": "3528233.3530732.pdf",
        "paper_id": "3528233.3530732",
        "source": {
            "pdf_number": "PDF-4",
            "pdf": "3528233.3530732.pdf",
            "title": "Neural Layered BRDFs",
            "lines": "102–106"
        },
        "expected_retrieval": ["layering network", "latent BRDF vectors", "random-walk simulation"],
        "gold_chunk_ids": ["3528233.3530732_chunk_004", "3528233.3530732_chunk_013", "3528233.3530732_chunk_026"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_034",
        "question_number": 34,
        "category": "Cross-Document Retrieval",
        "type": "cross_document",
        "difficulty": "hard",
        "question": "Compare how MoRF and Drivable Volumetric Avatars use volumetric representations.",
        "expected_answer": "MoRF uses a generative volumetric model to represent complete human heads with variable identities and multiview-consistent rendering. Drivable Volumetric Avatars uses a volumetric representation for articulated full-body avatars, combined with texel-aligned features to preserve information from driving signals.",
        "pdf_number": ["PDF-5", "PDF-6"],
        "pdf_filename": ["3528233.3530740.pdf", "3528233.3530753.pdf"],
        "paper_id": ["3528233.3530740", "3528233.3530753"],
        "sources": [
            {
                "pdf_number": "PDF-6",
                "pdf": "3528233.3530753.pdf",
                "title": "MoRF: Morphable Radiance Fields for Multiview Neural Head Modeling"
            },
            {
                "pdf_number": "PDF-5",
                "pdf": "3528233.3530740.pdf",
                "title": "Drivable Volumetric Avatars using Texel-Aligned Features"
            }
        ],
        "expected_retrieval": ["MoRF generative volumetric model", "texel-aligned features", "articulated full-body avatars"],
        "gold_chunk_ids": ["3528233.3530740_chunk_003", "3528233.3530740_chunk_010", "3528233.3530753_chunk_001", "3528233.3530753_chunk_010", "3528233.3530753_chunk_025"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_035",
        "question_number": 35,
        "category": "Cross-Document Retrieval",
        "type": "cross_document",
        "difficulty": "hard",
        "question": "Compare the role of latent representations in Neural Layered BRDFs and MoRF.",
        "expected_answer": "In Neural Layered BRDFs, the latent representation encodes BRDFs and allows the system to perform layering operations in latent space. In MoRF, each human identity is represented by a latent code within a shared volumetric model, allowing the model to represent multiple identities.",
        "pdf_number": ["PDF-4", "PDF-6"],
        "pdf_filename": ["3528233.3530732.pdf", "3528233.3530753.pdf"],
        "paper_id": ["3528233.3530732", "3528233.3530753"],
        "sources": [
            {
                "pdf_number": "PDF-4",
                "pdf": "3528233.3530732.pdf",
                "title": "Neural Layered BRDFs"
            },
            {
                "pdf_number": "PDF-6",
                "pdf": "3528233.3530753.pdf",
                "title": "MoRF: Morphable Radiance Fields for Multiview Neural Head Modeling"
            }
        ],
        "expected_retrieval": ["BRDFs in latent space", "identity represented by a latent code", "shared volumetric model"],
        "gold_chunk_ids": ["3528233.3530732_chunk_004", "3528233.3530732_chunk_013", "3528233.3530753_chunk_010", "3528233.3530753_chunk_026"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_036",
        "question_number": 36,
        "category": "Cross-Document Retrieval",
        "type": "cross_document",
        "difficulty": "hard",
        "question": "Compare the input signals used by the portrait animation system and the drivable avatar system.",
        "expected_answer": "The portrait-animation method uses a speech signal to predict facial landmark movements, which are then used to drive facial animation. The avatar method uses driving signals containing observed information about the performer, represented through texel-aligned features and combined with structural priors.",
        "pdf_number": ["PDF-2", "PDF-5"],
        "pdf_filename": ["3528233.3530720.pdf", "3528233.3530740.pdf"],
        "paper_id": ["3528233.3530720", "3528233.3530740"],
        "sources": [
            {
                "pdf_number": "PDF-2",
                "pdf": "3528233.3530720.pdf",
                "title": "Animating Portrait Line Drawings from a Single Face Photo and a Speech Signal"
            },
            {
                "pdf_number": "PDF-5",
                "pdf": "3528233.3530740.pdf",
                "title": "Drivable Volumetric Avatars using Texel-Aligned Features"
            }
        ],
        "expected_retrieval": ["speech signal to predict facial landmark movements", "texel-aligned features", "driving signals"],
        "gold_chunk_ids": ["3528233.3530720_chunk_009", "3528233.3530720_chunk_019", "3528233.3530740_chunk_003", "3528233.3530740_chunk_010"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_037",
        "question_number": 37,
        "category": "Cross-Document Retrieval",
        "type": "cross_document",
        "difficulty": "hard",
        "question": "Compare how the low-poly paper and Neural Layered BRDFs reduce computational complexity.",
        "expected_answer": "The low-poly method reduces geometric complexity by progressively simplifying a carved mesh using edge-collapse and edge-flip operations, then selecting from a Pareto set. Neural Layered BRDFs reduce the cost of layered-material evaluation by replacing expensive Monte Carlo/random-walk operations with neural operations in latent space.",
        "pdf_number": ["PDF-1", "PDF-4"],
        "pdf_filename": ["3528233.3530716.pdf", "3528233.3530732.pdf"],
        "paper_id": ["3528233.3530716", "3528233.3530732"],
        "sources": [
            {
                "pdf_number": "PDF-1",
                "pdf": "3528233.3530716.pdf",
                "title": "Low-poly Mesh Generation for Building Models"
            },
            {
                "pdf_number": "PDF-4",
                "pdf": "3528233.3530732.pdf",
                "title": "Neural Layered BRDFs"
            }
        ],
        "expected_retrieval": ["edge-collapse and edge-flip", "Pareto set", "replacing expensive random-walk", "latent space"],
        "gold_chunk_ids": ["3528233.3530716_chunk_002", "3528233.3530716_chunk_038", "3528233.3530732_chunk_004", "3528233.3530732_chunk_009"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_038",
        "question_number": 38,
        "category": "Adversarial Retrieval",
        "type": "adversarial",
        "difficulty": "hard",
        "question": "Since the low-poly building paper uses NeRF, how does its NeRF architecture generate building silhouettes?",
        "expected_answer": "The premise is false. The paper does not describe using NeRF for its visual hull. It constructs the visual hull using 3D primitives and Boolean intersections of input silhouettes.",
        "pdf_number": "PDF-1",
        "pdf_filename": "3528233.3530716.pdf",
        "paper_id": "3528233.3530716",
        "source": {
            "pdf_number": "PDF-1",
            "pdf": "3528233.3530716.pdf",
            "title": "Low-poly Mesh Generation for Building Models",
            "lines": "25–33"
        },
        "false_premise": True,
        "answerable": True,
        "expected_rag_behavior": "Do not hallucinate a NeRF architecture. Clarify that the premise is false and the method uses Boolean intersections of 3D extruded silhouettes.",
        "expected_retrieval": ["Boolean intersecting", "visual hull", "silhouettes"],
        "gold_chunk_ids": ["3528233.3530716_chunk_002", "3528233.3530716_chunk_009"]
    },
    {
        "id": "rag_039",
        "question_number": 39,
        "category": "Adversarial Retrieval",
        "type": "adversarial",
        "difficulty": "hard",
        "question": "The portrait-animation method predicts facial landmarks directly from the input photograph. How does this work?",
        "expected_answer": "The premise is incorrect. The method predicts facial landmark movements from the speech signal. It uses the speech-to-facial-landmark translation module from MakeItTalk.",
        "pdf_number": "PDF-2",
        "pdf_filename": "3528233.3530720.pdf",
        "paper_id": "3528233.3530720",
        "source": {
            "pdf_number": "PDF-2",
            "pdf": "3528233.3530720.pdf",
            "title": "Animating Portrait Line Drawings from a Single Face Photo and a Speech Signal",
            "lines": "236–247"
        },
        "false_premise": True,
        "answerable": True,
        "expected_rag_behavior": "Clarify that landmarks are predicted from speech via MakeItTalk, not directly from the input photograph.",
        "expected_retrieval": ["speech to facial landmark", "MakeItTalk"],
        "gold_chunk_ids": ["3528233.3530720_chunk_009", "3528233.3530720_chunk_019"]
    },
    {
        "id": "rag_040",
        "question_number": 40,
        "category": "Adversarial Retrieval",
        "type": "adversarial",
        "difficulty": "hard",
        "question": "Since MoRF uses StyleGAN2, how does its StyleGAN generator maintain multiview consistency?",
        "expected_answer": "This contains a false premise. StyleGAN2 is discussed as related/background work. MoRF instead extends NeRF into a morphable generative neural model for multiview-consistent human-head rendering.",
        "pdf_number": "PDF-6",
        "pdf_filename": "3528233.3530753.pdf",
        "paper_id": "3528233.3530753",
        "source": {
            "pdf_number": "PDF-6",
            "pdf": "3528233.3530753.pdf",
            "title": "MoRF: Morphable Radiance Fields for Multiview Neural Head Modeling",
            "lines": "24–36"
        },
        "false_premise": True,
        "answerable": True,
        "expected_rag_behavior": "Do not hallucinate StyleGAN generator architecture for MoRF. MoRF extends NeRF, not StyleGAN.",
        "expected_retrieval": ["StyleGAN2", "extends NeRF", "multiview-consistent"],
        "gold_chunk_ids": ["3528233.3530753_chunk_001", "3528233.3530753_chunk_010", "3528233.3530753_chunk_019"]
    },
    {
        "id": "rag_041",
        "question_number": 41,
        "category": "Adversarial Retrieval",
        "type": "adversarial",
        "difficulty": "hard",
        "question": "Why does Neural Layered BRDFs perform Monte Carlo random walks during every final evaluation?",
        "expected_answer": "The premise is false. The proposed method is designed to replace expensive random-walk computation with a neural layering operation in latent space.",
        "pdf_number": "PDF-4",
        "pdf_filename": "3528233.3530732.pdf",
        "paper_id": "3528233.3530732",
        "source": {
            "pdf_number": "PDF-4",
            "pdf": "3528233.3530732.pdf",
            "title": "Neural Layered BRDFs",
            "lines": "102–106"
        },
        "false_premise": True,
        "answerable": True,
        "expected_rag_behavior": "Identify that the premise is false; the method avoids Monte Carlo random walks during evaluation.",
        "expected_retrieval": ["replacing expensive random-walk", "neural layering"],
        "gold_chunk_ids": ["3528233.3530732_chunk_004", "3528233.3530732_chunk_009", "3528233.3530732_chunk_013"]
    },
    {
        "id": "rag_042",
        "question_number": 42,
        "category": "Adversarial Retrieval",
        "type": "adversarial",
        "difficulty": "hard",
        "question": "What high-quality mesh-tracking algorithm is required before the avatar model can operate?",
        "expected_answer": "The premise is false. The paper explicitly states that its volumetric representation does not require high-quality mesh tracking as a prerequisite.",
        "pdf_number": "PDF-5",
        "pdf_filename": "3528233.3530740.pdf",
        "paper_id": "3528233.3530740",
        "source": {
            "pdf_number": "PDF-5",
            "pdf": "3528233.3530740.pdf",
            "title": "Drivable Volumetric Avatars using Texel-Aligned Features",
            "lines": "75–79"
        },
        "false_premise": True,
        "answerable": True,
        "expected_rag_behavior": "Identify that high-quality mesh tracking is not required, as the volumetric representation avoids this limitation.",
        "expected_retrieval": ["mesh-based approaches require accurate tracking", "volumetric representation"],
        "gold_chunk_ids": ["3528233.3530740_chunk_010", "3528233.3530740_chunk_014"]
    },
    {
        "id": "rag_043",
        "question_number": 43,
        "category": "Adversarial Retrieval",
        "type": "adversarial",
        "difficulty": "hard",
        "question": "The HDR paper shows that image-quality metrics reliably rank all six methods. What evidence supports this?",
        "expected_answer": "The premise is false. The paper reports that metric predictions correlate poorly with subjective quality scores and emphasizes limitations of existing metrics.",
        "pdf_number": "PDF-3",
        "pdf_filename": "3528233.3530729.pdf",
        "paper_id": "3528233.3530729",
        "source": {
            "pdf_number": "PDF-3",
            "pdf": "3528233.3530729.pdf",
            "title": "Comparison of single image HDR reconstruction methods — the caveats of quality assessment",
            "lines": "55–79"
        },
        "false_premise": True,
        "answerable": True,
        "expected_rag_behavior": "Identify that metrics do NOT reliably rank methods; correlation with human subjective scores is poor.",
        "expected_retrieval": ["metric predictions correlate poorly", "subjective quality"],
        "gold_chunk_ids": ["3528233.3530729_chunk_002", "3528233.3530729_chunk_008", "3528233.3530729_chunk_043", "3528233.3530729_chunk_048"]
    },
    {
        "id": "rag_044",
        "question_number": 44,
        "category": "Negative / Unanswerable Tests",
        "type": "negative",
        "difficulty": "medium",
        "question": "What was the annual licensing fee charged to mobile game developers for using the low-poly mesh algorithm?",
        "expected_answer": "Not answerable from the provided PDFs.",
        "pdf_number": "PDF-1",
        "pdf_filename": "3528233.3530716.pdf",
        "paper_id": "3528233.3530716",
        "source": {
            "pdf_number": "PDF-1",
            "pdf": "3528233.3530716.pdf",
            "title": "Low-poly Mesh Generation for Building Models"
        },
        "false_premise": False,
        "answerable": False,
        "expected_rag_behavior": "System should state that no information is found in the provided documents, abstaining from answering.",
        "expected_retrieval": [],
        "gold_chunk_ids": []
    },
    {
        "id": "rag_045",
        "question_number": 45,
        "category": "Negative / Unanswerable Tests",
        "type": "negative",
        "difficulty": "medium",
        "question": "What was the salary of the researchers who developed MoRF?",
        "expected_answer": "Not answerable from the provided PDFs.",
        "pdf_number": "PDF-6",
        "pdf_filename": "3528233.3530753.pdf",
        "paper_id": "3528233.3530753",
        "source": {
            "pdf_number": "PDF-6",
            "pdf": "3528233.3530753.pdf",
            "title": "MoRF: Morphable Radiance Fields for Multiview Neural Head Modeling"
        },
        "false_premise": False,
        "answerable": False,
        "expected_rag_behavior": "System should state that no information is found in the provided documents, abstaining from answering.",
        "expected_retrieval": [],
        "gold_chunk_ids": []
    },
    {
        "id": "rag_046",
        "question_number": 46,
        "category": "Negative / Unanswerable Tests",
        "type": "negative",
        "difficulty": "medium",
        "question": "What was the exact retail price of the GPU used to train MoRF?",
        "expected_answer": "Not answerable from the provided PDFs.",
        "pdf_number": "PDF-6",
        "pdf_filename": "3528233.3530753.pdf",
        "paper_id": "3528233.3530753",
        "source": {
            "pdf_number": "PDF-6",
            "pdf": "3528233.3530753.pdf",
            "title": "MoRF: Morphable Radiance Fields for Multiview Neural Head Modeling"
        },
        "false_premise": False,
        "answerable": False,
        "expected_rag_behavior": "System should state that no information is found in the provided documents, abstaining from answering.",
        "expected_retrieval": [],
        "gold_chunk_ids": []
    },
    {
        "id": "rag_047",
        "question_number": 47,
        "category": "Negative / Unanswerable Tests",
        "type": "negative",
        "difficulty": "medium",
        "question": "How much revenue did Meta generate from the Drivable Volumetric Avatars project?",
        "expected_answer": "Not answerable from the provided PDFs.",
        "pdf_number": "PDF-5",
        "pdf_filename": "3528233.3530740.pdf",
        "paper_id": "3528233.3530740",
        "source": {
            "pdf_number": "PDF-5",
            "pdf": "3528233.3530740.pdf",
            "title": "Drivable Volumetric Avatars using Texel-Aligned Features"
        },
        "false_premise": False,
        "answerable": False,
        "expected_rag_behavior": "System should state that no information is found in the provided documents, abstaining from answering.",
        "expected_retrieval": [],
        "gold_chunk_ids": []
    },
    {
        "id": "rag_048",
        "question_number": 48,
        "category": "Negative / Unanswerable Tests",
        "type": "negative",
        "difficulty": "medium",
        "question": "What was the home address of the corresponding author of Neural Layered BRDFs?",
        "expected_answer": "Not answerable from the provided PDFs.",
        "pdf_number": "PDF-4",
        "pdf_filename": "3528233.3530732.pdf",
        "paper_id": "3528233.3530732",
        "source": {
            "pdf_number": "PDF-4",
            "pdf": "3528233.3530732.pdf",
            "title": "Neural Layered BRDFs"
        },
        "false_premise": False,
        "answerable": False,
        "expected_rag_behavior": "System should state that no information is found in the provided documents, abstaining from answering.",
        "expected_retrieval": [],
        "gold_chunk_ids": []
    },
    {
        "id": "rag_049",
        "question_number": 49,
        "category": "Needle in Haystack",
        "type": "needle_in_haystack",
        "difficulty": "hard",
        "question": "What percentage of the low-poly building dataset was non-manifold and what percentage was non-watertight?",
        "expected_answer": "The dataset contained: 39% non-manifold models and 88% non-watertight models.",
        "pdf_number": "PDF-1",
        "pdf_filename": "3528233.3530716.pdf",
        "paper_id": "3528233.3530716",
        "source": {
            "pdf_number": "PDF-1",
            "pdf": "3528233.3530716.pdf",
            "title": "Low-poly Mesh Generation for Building Models",
            "lines": "637–642"
        },
        "expected_retrieval": ["39% (resp. 88%) are non-manifold (resp. non-watertight)", "39%", "88%"],
        "gold_chunk_ids": ["3528233.3530716_chunk_048"],
        "answerable": True,
        "false_premise": False
    },
    {
        "id": "rag_050",
        "question_number": 50,
        "category": "Detailed Technical",
        "type": "detailed_technical",
        "difficulty": "hard",
        "question": "What strategy does the low-poly method use when deciding which edge to collapse?",
        "expected_answer": "For edge-collapse, the method uses QEM (Quadric Error Metrics) to rank the edges and adds a virtual perpendicular plane with a small weight to combat coplanar degeneracy.",
        "pdf_number": "PDF-1",
        "pdf_filename": "3528233.3530716.pdf",
        "paper_id": "3528233.3530716",
        "source": {
            "pdf_number": "PDF-1",
            "pdf": "3528233.3530716.pdf",
            "title": "Low-poly Mesh Generation for Building Models",
            "lines": "569–580"
        },
        "expected_retrieval": ["QEM", "virtual perpendicular plane", "coplanar degeneracy"],
        "gold_chunk_ids": ["3528233.3530716_chunk_042"],
        "answerable": True,
        "false_premise": False
    }
]

# File 1: Comprehensive Evaluation Dataset JSON
dataset_full = {
    "dataset_name": "SIGGRAPH RAG Benchmark Evaluation Dataset",
    "version": "1.0.0",
    "description": "Comprehensive benchmark dataset with 50 evaluation items covering exact facts, semantic search, multi-hop, keyword mismatch, numerical retrieval, long context, ambiguity, cross-document comparison, adversarial robustness, negative/unanswerable tests, and needle-in-haystack scenarios across 6 SIGGRAPH papers.",
    "pdf_catalog": pdf_catalog,
    "category_summary": {
        "exact_fact": 8,
        "semantic": 5,
        "multi_hop": 4,
        "keyword_mismatch": 5,
        "numerical": 4,
        "long_context": 4,
        "ambiguous": 3,
        "cross_document": 4,
        "adversarial": 6,
        "negative": 5,
        "needle_in_haystack": 1,
        "detailed_technical": 1,
        "total": 50
    },
    "prioritized_benchmark_subset_10": ["rag_001", "rag_009", "rag_014", "rag_018", "rag_027", "rag_029", "rag_031", "rag_034", "rag_038", "rag_044"],
    "questions": questions_data
}

full_dataset_path = eval_dir / "siggraph_rag_eval_dataset.json"
with open(full_dataset_path, "w", encoding="utf-8") as f:
    json.dump(dataset_full, f, indent=2, ensure_ascii=False)
print(f"Saved {full_dataset_path} ({len(questions_data)} questions)")

# File 2: Executable Runner JSON (Evret / evaluate.py / RAG QA runner compatible)
runner_queries = []
for q in questions_data:
    item = {
        "query_id": q["id"],
        "question_number": q["question_number"],
        "query_text": q["question"],
        "pdf_number": q["pdf_number"],
        "paper_id": q["paper_id"],
        "pdf_filename": q["pdf_filename"],
        "type": q["type"],
        "category": q["category"],
        "difficulty": q["difficulty"],
        "expected_answers": [q["expected_answer"]],
        "expected_doc_ids": q["gold_chunk_ids"],
        "expected_retrieval": q.get("expected_retrieval", []),
        "answerable": q["answerable"],
        "false_premise": q["false_premise"]
    }
    if "source" in q:
        item["reference_lines"] = q["source"].get("lines")
        item["paper_title"] = q["source"].get("title")
    runner_queries.append(item)

runner_data = {
    "benchmark_name": "siggraph_rag_evaluation_50q",
    "total_queries": len(runner_queries),
    "queries": runner_queries
}

runner_path = eval_dir / "siggraph_rag_eval_run.json"
with open(runner_path, "w", encoding="utf-8") as f:
    json.dump(runner_data, f, indent=2, ensure_ascii=False)
print(f"Saved {runner_path} ({len(runner_queries)} queries)")
