class GenerateInitialSchemaFromDBDiagram < ActiveRecord::Migration[6.1]
    def change
        create_table :doctor do |t|
            t.uuid :id
            t.string :name
            t.text :description
            t.string :brand
            t.integer :plate

            t.timestamps
        end

        create_table :appointment do |t|
            t.uuid :id
            t.uuid :patient_id
            t.uuid :doctor_id
            t.datetime :scheduled_at

            t.timestamps
        end

        create_table :patient do |t|
            t.uuid :id
            t.string :name
            t.text :description

            t.timestamps
        end

        add_foreign_key :patient, :appointment, column: :id, primary_key: :patient_id
        add_index :patient, :appointment

        add_foreign_key :doctor, :appointment, column: :id, primary_key: :doctor_id
        add_index :doctor, :appointment
    end
end
