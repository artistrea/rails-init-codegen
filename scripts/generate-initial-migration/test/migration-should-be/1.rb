class GenerateInitialSchemaFromDBDiagram < ActiveRecord::Migration[6.1]
    def change
      create_table :cars do |t|
        t.string :name
        t.text :description

        t.timestamps
      end

      create_table :cars do |t|
        t.string :name
        t.text :description
        t.string :brand
        t.integer :plate

        t.timestamps
      end
    end
end
