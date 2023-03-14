STATES = {
    "UNSCOPED": 0,
    "TABLE:INITIALIZING": 1,
    "TABLE:SCOPED": 2,
    "TABLE:ADDING_ATTRIBUTE": 3
}

ADDITION_TYPES = {
    "TABLE": 0,
    "LINE": 1
}

TOKENS = {
    "NEW_TABLE": ["Table"],
    "ENTER_SCOPE": ["{"],
    "ESCAPE_SCOPE": ["}"],
    "ATTRIBUTE_TYPE": ["text", "string"]
}

class FileParser:
    def build(self, file):
        self.cur_state = STATES["UNSCOPED"]
        self.cur_state_info = {}
        self.file = file
        self.schema_obj = {"TABLES": {}}
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
    def default_schema_lines(_self, ):
        "class GenerateInitialSchemaFromDBDiagram < ActiveRecord::Migration[6.1]def change
      create_table :cars do |t|
        t.string :name
        t.text :description
  
        t.timestamps
      end
    end
end
  "
    def build(self, schema_obj):
        self.schema_obj = schema_obj


    def write_to_file(self, filename):

        


with open("scripts/generate-initial-migration/dbdiagram.txt") as f:
    schema_obj = FileParser() \
        .build(f)           \
        .parse_file()

    RAILS_VERSION = "6.1"

    ObjToMigrationStr()\
        .build(schema_obj)\
        .write_to_file("scripts/generate-initial-migration/migration.rb")
