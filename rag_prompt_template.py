relation_list = [
    "temporally follows",
    "after",
    "due to",
    "has realization",
    "associated with",
    "has definitional manifestation",
    "associated finding",
    "associated aetiologic finding",
    "associated etiologic finding",
    "interprets",
    "associated morphology",
    "causative agent",
    "course",
    "finding site",
    "temporally related to",
    "pathological process",
    "direct morphology",
    "is modification of",
    "measures",
    "direct substance",
    "has active ingredient",
    "using",
    "part of"
]

# ======================================
# MIMIC-IV snomed entity extraction
# ======================================
MIMICIV_entity_extraction_prompt = """\
Here is the context: {text}.\

Task: Extract the SNOMED CT concepts from the given context.\

The steps are as follows:\
1. extract the concepts from the given context sentence, using the retrieved triplets.
2. there may be abbreviations or acronyms in the context, extract them as concepts as well if they are related to the concepts.
3. output the concepts in a list [] strictly, each concept is separated by a comma.\
\

Provide your answer as follows:

Answer:::
Concepts: [] \
Answer End:::\

Requirements:\
You MUST provide values for 'Concepts:' in your answer. \
ONLY extract concepts, DO NOT include the type of the concept, reasoning, or any other information. \
DO NOT include mark numbers or ordinal numbers in your answer. \
Extract as many unique concepts as possible from the given context. \

"""

# ======================================
# snomed concepts extraction
# ======================================
snomed_extraction_prompt = """\
Here is the context: {text}.\

Task: Extract the SNOMED CT triplets from the given context with the format of (concept ; is ; type).\

Here is the optional type list: [disorder, clinical finding, substance, morphologically abnormal structures, organism].\

The steps are as follows:\
1. extract the concept from the given context sentence, using the retrieved sub-graph.
2. select the most likely type from the list for the extracted concept.
3. output the triplets in the format of (concept ; is ; type) strictly.\
\

triplets:\

\

Note: Only output the triplets.\

"""

# ======================================
# BC5CDR entity-type extraction
# ======================================
BC5CDR_extraction_prompt = """\
Here is the context: {text}.\

Task: Extract the entity-type pairs from the given context with the format of (entity ; type).\

Here is the type list: [Disorder, Substance].\

The steps are as follows:\
1. extract the entity from the given context abstract, using the retrieved sub-graph.
2. select ONE most likely type from the list for the extracted entity.
3. output the pairs in the format of (entity ; type) strictly.
4. repeat the step 1 to step 3.\
\

Provide your answer as follows:

Answer:::
Pairs: (All extracted pairs)\
Answer End:::\

Requirements:\
You MUST provide values for 'Pairs:' in your answer. \
ONLY use the type in the type list: [Disorder, Substance].\
Extract as many valid entity-type pairs as possible from the given context abstract.\

"""
# ======================================
# MIMIC-IV entity-type extraction
# ======================================
MIMICIV_extraction_prompt = """\

Here is the context: {text}.\

Task: Extract the entity-type pairs from the given context with the format of (entity ; type).\

Here is the type list: [finding, disorder, procedure, regime/therapy, morphologic abnormality, body structure, cell structure].\

The steps are as follows:\
1. extract the entity from the given context abstract, using the retrieved sub-graph.
2. select ONE most likely type from the list for the extracted entity.
3. output the pairs in the format of (entity ; type) strictly.
4. repeat the step 1 to step 3.\
\
Provide your answer as follows:

Answer:::
Pairs: (All extracted pairs)\
Answer End:::\
\

Requirements:\
You MUST provide values for 'Pairs:' in your answer. \
output the pairs in the format of (entity ; type) strictly. \

"""


# ======================================
# MIMIC-IV entity-type extraction with additional entities
# ======================================
MIMICIV_extraction_prompt_with_entities = """\
You are a medical professional working in a hospital. You have been given a discharge note, a list of entities, and a list of types. Your task is to link the entities to the most likely type from the type list.

Here is the abstract: {text}.\

Here is the type list: [finding, disorder, procedure, regime/therapy, morphologic abnormality, body structure, cell structure].\

Here is the list of entities for consideration: {entities}.\

Task: link the entity and the type and output entity-type pairs with the format of (entity ; type).\

The steps are as follows:
1. for each entity in {entities}, link it to the most likely type from the type list. if you cannot find a suitable type, ignore the entity.
2. if you find more entities in the abstract, extract them and link them to the most likely type.
3. output the pairs in the format of (entity ; type) strictly.\
\

Provide your answer as follows:

Answer:::
Pairs: (entity ; type)
Answer End:::\

Requirements:
You MUST provide values for 'Pairs:' in your answer. 
ONLY output valid entity-type pairs without any reasoning. 

"""

prompt_var_mappings = {"text": "text"}
