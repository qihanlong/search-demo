from pathlib import Path
import tantivy

def getSchema():
    schema_builder = tantivy.SchemaBuilder()
    schema_builder.add_text_field("title", stored=True)
    schema_builder.add_text_field("body", stored=True)
    schema_builder.add_text_field("url",stored=True)
    schema_builder.add_text_field("text",stored=True)
    schema_builder.add_date_field("retrieval_date",stored=True)
    schema = schema_builder.build()
    return schema

def getIndex(path_root='.', schema=None):
    if not schema:
        schema = getSchema()

    # Creating our index (in memory)
    index = tantivy.Index(schema)

    index_path = Path(path_root) / "index"
    index_path.mkdir(exist_ok=True)
    persistent_index = tantivy.Index(schema, path=str(index_path))
    return persistent_index