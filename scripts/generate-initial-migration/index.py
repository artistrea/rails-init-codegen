STATES = {
    "UNSCOPED": 0,
    "TABLE:INITIALIZING": 1,
    "TABLE:SCOPED": 2,
    "TABLE:ADDING_ATTRIBUTE": 3,
    "REFERENCES:FIRST_TABLE": 4,
    "REFERENCES:RELATIONSHIP": 5,
    "REFERENCES:SECOND_TABLE": 6,
}

ADDITION_TYPES = {
    "TABLE": 0,
    "LINE": 1
}

TOKENS = {
    "NEW_TABLE": ["Table"],
    "ENTER_SCOPE": ["{"],
    "ESCAPE_SCOPE": ["}"],
    "REFERENCES": ["References"]
}

class FileParser:
    def build(self, file):
        self.cur_state = STATES["UNSCOPED"]
        self.cur_state_info = {}
        self.file = file
        self.schema_obj = {"TABLES": {}, "RELATIONSHIPS": []}
        return self

    def read_line(self, line):
        line = line.strip()
        tokens = line.split()
        for i, token in enumerate(tokens):
            token = token.strip(",")
            self.mutate_schema_obj(token, i)
            

    def mutate_schema_obj(self, token, token_position):
        if self.cur_state == STATES["UNSCOPED"]:
            if token_position == 0 and token in TOKENS["NEW_TABLE"]:
                self.cur_state = STATES["TABLE:INITIALIZING"]
            if token_position == 0 and token in TOKENS["REFERENCES"]:
                self.cur_state = STATES["REFERENCES:FIRST_TABLE"]

        elif self.cur_state == STATES["TABLE:INITIALIZING"]:
            if token in TOKENS["ENTER_SCOPE"]:
                self.cur_state = STATES["TABLE:SCOPED"]
            else:
                self.add_table(token, token_position)


        elif self.cur_state == STATES["TABLE:SCOPED"]:
            if token in TOKENS["ESCAPE_SCOPE"]:
                self.cur_state = STATES["UNSCOPED"]
            else:
                self.add_attribute(token, token_position)
                self.cur_state = STATES["TABLE:ADDING_ATTRIBUTE"]

        elif self.cur_state == STATES["TABLE:ADDING_ATTRIBUTE"]:
            self.add_attribute(token, token_position)

        elif self.cur_state == STATES["REFERENCES:FIRST_TABLE"]:
            [table_name, column_name] = token.split(".")
            self.cur_state_info = { "references_first_table": table_name, "references_first_column": column_name }
            self.cur_state = STATES["REFERENCES:RELATIONSHIP"]

        elif self.cur_state == STATES["REFERENCES:RELATIONSHIP"]:
            self.cur_state_info["references_relationship"] =  token
            self.cur_state = STATES["REFERENCES:SECOND_TABLE"]

        elif self.cur_state == STATES["REFERENCES:SECOND_TABLE"]:
            [table_name, column_name] = token.split(".")
            self.cur_state_info["references_second_table"] = table_name
            self.cur_state_info["references_second_column"] = column_name
            self.add_relationship(token, token_position)
            self.cur_state = STATES["UNSCOPED"]


    def add_relationship(self, token, token_position):
        if token_position != 3:
            raise Exception(f"Há tokens demais ao criar a referência em {token}")
        # TODO: validar mais coisas

        self.schema_obj["RELATIONSHIPS"].append(self.cur_state_info)
        self.cur_state_info = {}

    def add_table(self, token, token_position):
        self.cur_state_info = { "table_name": token }

        if token_position != 1 and token not in TOKENS["ENTER_SCOPE"]:
            raise Exception(f"Há mais de uma palavra como nome de uma tabela em {token}")
        if token in self.schema_obj["TABLES"].keys():
            raise Exception(f"Tabela {token} repetida")

        self.schema_obj["TABLES"][token] = {}

    def add_attribute(self, token, token_position):
        if self.cur_state == STATES["TABLE:SCOPED"]:
            self.schema_obj["TABLES"]\
                [self.cur_state_info["table_name"]] \
                    [token] = {}
            self.cur_state = STATES["TABLE:ADDING_ATTRIBUTE"]
            self.cur_state_info["attribute_name"] = token

        elif self.cur_state == STATES["TABLE:ADDING_ATTRIBUTE"]:
            self.schema_obj["TABLES"]\
                [self.cur_state_info["table_name"]] \
                    [self.cur_state_info["attribute_name"]] \
                        ["type"] = token

        LAST_ATTRIBUTE_TOKEN_POS = 1
        if token_position == LAST_ATTRIBUTE_TOKEN_POS:
            self.cur_state = STATES["TABLE:SCOPED"]


    def parse_file(self):
        for line in self.file:
            self.read_line(line)
        return self.schema_obj


class ObjToMigrationStr:
    def build(self, schema_obj):
        self.schema_obj = schema_obj
        return self

    def create_field(self, field_name, field_type):
        return f"t.{field_type} :{field_name.lower()}"

    def create_table(self, table_name):
        newl = '\n            '
        content = f"""
        create_table :{table_name.lower()} do |t|
            {newl.join(map(lambda field_name: self.create_field(field_name, self.schema_obj["TABLES"][table_name][field_name]["type"]), self.schema_obj["TABLES"][table_name].keys()))}

            t.timestamps
        end"""
        return content

    def create_reference(self, reference):
        if reference["references_relationship"] not in ["-", "<", ">"]:
            raise Exception(f"A seguinte referência utiliza um relacionamento inválido: {reference}")
        if reference["references_relationship"] == ">":
            # @important: para não mutar o objeto original
            reference = reference.copy()
            reference["references_relationship"] = "<"
            reference["references_first_table"], reference["references_second_table"] = reference["references_second_table"], reference["references_first_table"]
            reference["references_first_column"], reference["references_second_column"] = reference["references_second_column"], reference["references_first_column"]

        # TODO: validar se tabelas e colunas existem
        # TODO: usar uma função camelCaseToSnakeCase ao invés de .lower()
        fk_content = f"""add_foreign_key :{reference['references_first_table'].lower()}, :{reference['references_second_table'].lower()}, column: :{reference['references_first_column']}, primary_key: :{reference['references_second_column']}"""
        index_content = f"add_index :{reference['references_first_table'].lower()}, :{reference['references_second_table'].lower()}"

        return '\n        '.join([fk_content, index_content])

    def write_migration_to_file(self, filename):
        newl = '\n'
        newl_w_tab = '\n\n        '
        content = f"""class GenerateInitialSchemaFromDBDiagram < ActiveRecord::Migration[6.1]
    def change{newl.join(map(self.create_table, self.schema_obj["TABLES"].keys()))}

        {newl_w_tab.join(map(self.create_reference, self.schema_obj["RELATIONSHIPS"]))}
    end
end
"""

        with open(filename, "w") as f:
            f.write(content)
        return self

    def write_models_to_folder(self, dirname):
        for model_name in self.schema_obj["TABLES"].keys():
            self.write_model_to_file(dirname + f"/{model_name}.rb", model_name)
    
    def write_model_to_file(self, filename, model_name):
        # newl = '\n'
        # newl_w_tab = '\n\n        '
#         references_relationship
# references_second_table
# references_second_column
        # has_one = filter(
        #     lambda relation: (model_name, "-") == (relation["references_first_table"],relation["references_relationship"]),
        #     self.schema_obj["RELATIONSHIPS"])
        content = f"""class {model_name} < ApplicationRecord
end
"""

        with open(filename, "w") as f:
            f.write(content)
        return self

        


# TODO: refatorar interfaces
with open("scripts/generate-initial-migration/dbdiagram2.txt") as f:
    schema_obj = FileParser() \
        .build(f)           \
        .parse_file()

    print(schema_obj)

    # RAILS_VERSION = "6.1"

    ObjToMigrationStr()\
        .build(schema_obj)\
        .write_migration_to_file("scripts/generate-initial-migration/migration.rb")\
        .write_models_to_folder("scripts/generate-initial-migration/models")
