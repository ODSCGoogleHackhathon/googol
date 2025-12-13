import sqlite3

class AnnotationRepo:
    
    def __init__(self):
        self.connection = sqlite3.connect('./DB/annotations.db')
        self.cursor = self.connection.cursor()
    
    def save_annotations(self, set_name:str, data: list[list]):
        """
        Adds new annotations to the database.

        :param set_name: set identifier. Use this for different datasets.
        :type set_name: str
        :param data: list of lists with all the annotations to register. Each list should hold ["path", "label", "patient_id", "desc"].
        :type data: list[dict]

        > PS: labels and patients must be registered before annotations are saved.
        """

        self.cursor.executemany('INSERT INTO annotation VALUES (?, ?, ?, ?, ?)', [[set_name] + content for content in data])
        self.connection.commit()
    
    def update_annotation(self, set_name:str, path:str, new_label:str, new_desc:str):
        """
        Updates an annotation.

        :param set_name: set identifier.
        :type set_name: str
        :param path: file path.
        :type path: str
        :param new_label: updated label name.
        :type new_label: str
        :param new_desc: updated description string.
        :type new_desc: str
        """
        self.cursor.execute('UPDATE annotation SET label=?, desc=? WHERE set_name=? AND path_url=?', 
                            [new_label, new_desc, set_name, path])
        self.connection.commit()

    def delete_annotation(self, set_name:str, path:str):
        """
        Deletes an annoation.
        
        :param set_name: set id.
        :type set_name: str
        :param path: file path.
        :type path: str
        """
        self.cursor.execute('DELETE FROM annotation WHERE set_name=? AND path_url=?', [set_name, path])
        self.connection.commit()

    def get_annotations(self, set_name:str, paths:list[str]|None=None):
        """
        Retrieves annotations for a specific set. Returns a list of annotations.
        
        :param self: Description
        :param set_name: Description
        :type set_name: str
        :param paths: a list of paths for annotations to be retrieved or None, to retrieve all of them.
        :type paths: list[str]|None
        """
        if paths is None:
            res = self.cursor.execute('SELECT * FROM annotation WHERE set_name=?', set_name)
        else:
            res = self.cursor.execute(f'SELECT * FROM annotation WHERE set_name=? AND path_url IN ({','.join(['?']*len(paths))})', [set_name] + paths) # based on https://stackoverflow.com/questions/5766230/select-from-sqlite-table-where-rowid-in-list-using-python-sqlite3-db-api-2-0
        return res.fetchall()

    def add_label(self, label_name:str):
        """
        Register a label.
        
        :param label_name: label name.
        :type label_name: str
        """

        self.cursor.execute('INSERT INTO label VALUES (?)', label_name)
        self.connection.commit()

    def add_patient(self, patient_id:int, patient_name:str):
        """
        Register a patient.

        :param patient_id: patient id.
        :type patient_id: int
        :param patient_name: patient name.
        :type patient_name: str
        """
        self.cursor.execute('INSERT INTO patient VALUES (?, ?)', patient_id, patient_name)
        self.connection.commit()

    def update_label(self, label_name:str, new_name:str):
        """
        Update label name.
        
        :param label_name: label name.
        :type label_name: str
        :param new_name: new label name.
        :type new_name: str
        """
        self.cursor.execute('UPDATE label SET name=? WHERE name=?', [new_name, label_name])
        self.connection.commit()

    def update_patient(self, patient_id, patient_name:str, new_name:str):
        """
        Update patient name.
        
        :param patient_name: patient name.
        :type patient_name: str
        :param new_name: new patient name.
        :type new_name: str
        """
        self.cursor.execute('UPDATE patient SET name=? WHERE id=? AND name=?', [new_name, patient_id, patient_name])
        self.connection.commit()
        
    def get_labels(self):
        """
        Get labels.
        """
        res = self.connection.execute('SELECT * FROM label')
        return res.fetchall()
    
    def get_patients(self):
        """
        Get patients.
        """
        res = self.connection.execute('SELECT * FROM patient')
        return res.fetchall()




# Examples
#repo = AnnotationRepo()
#repo.save_annotations('1', [['/a.jpg', 'default', 1, 'none'], ['/b.jpg', 'default', 1, 'none as well']])
#print(repo.get_annotations('1'))
#print(repo.get_annotations('1', ['/b.jpg']))
#repo.update_annotation('1', '/b.jpg', 'cool_label', 'new description')
#repo.delete_annotation('1', '/a.jpg')