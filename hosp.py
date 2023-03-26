
import random
import simpy

SIM_TIME = 1500  # extend simulation time to 500 time units

class EmergencyDepartment:
    def __init__(self, env, num_beds):
        self.env = env
        self.num_beds = num_beds
        self.beds = simpy.Resource(env, capacity=num_beds)
        self.wait_times = []

    def treat_patient(self, patient):
        with self.beds.request() as req:
            yield req
            self.wait_times.append(self.env.now - patient.arrival_time)
            yield self.env.timeout(random.expovariate(1/8))   # increase treatment time for emergency patients

class InpatientDepartment:
    def __init__(self, env, num_beds):
        self.env = env
        self.num_beds = num_beds
        self.beds = simpy.Resource(env, capacity=num_beds)
        self.wait_times = []

    def treat_patient(self, patient):
        with self.beds.request() as req:
            yield req
            self.wait_times.append(self.env.now - patient.arrival_time)
            yield self.env.timeout(random.expovariate(1/10))   # decrease treatment time for inpatient patients

class OutpatientDepartment:
    def __init__(self, env, num_exam_rooms):
        self.env = env
        self.num_exam_rooms = num_exam_rooms
        self.exam_rooms = simpy.Resource(env, capacity=num_exam_rooms)
        self.wait_times = []

    def treat_patient(self, patient):
        with self.exam_rooms.request() as req:
            yield req
            start_time = self.env.now
            self.wait_times.append(start_time - patient.arrival_time)
            yield self.env.timeout(random.expovariate(1/10))
            end_time = self.env.now
            self.wait_times[-1] += end_time - start_time

class Patient:
    def __init__(self, patient_type, arrival_time):
        self.patient_type = patient_type
        self.arrival_time = arrival_time


class Hospital:
    def __init__(self, env):
        self.env = env
        self.emergency_dept = EmergencyDepartment(env, 40)   # increase number of beds in emergency department
        self.inpatient_dept = InpatientDepartment(env, 10)   # decrease number of beds in inpatient department
        self.outpatient_dept = OutpatientDepartment(env, 20)
        self.wait_times_emergency = []
        self.wait_times_inpatient = []
        self.wait_times_outpatient = []
        self.utilization_emergency = 0
        self.utilization_inpatient = 0
        self.utilization_outpatient = 0

    def generate_patients(self):
        while True:
            patient_type = random.choices(['emergency', 'inpatient', 'outpatient'], weights=[0.3, 0.2, 0.5])[0]

            arrival_time = self.env.now
            patient = Patient(patient_type=patient_type, arrival_time=arrival_time)
            if patient_type == 'emergency':
              self.env.process(self.emergency_dept.treat_patient(patient))
            elif patient_type == 'inpatient':
              self.env.process(self.inpatient_dept.treat_patient(patient))
            else:
              self.env.process(self.outpatient_dept.treat_patient(patient))
              yield self.env.timeout(random.expovariate(4.6)) # adjust patient arrival rate based on hospital demand

            
    def collect_statistics(self):
      while True:
          if len(self.emergency_dept.wait_times) > 0:
              self.wait_times_emergency.append(sum(self.emergency_dept.wait_times) / len(self.emergency_dept.wait_times))
          if len(self.inpatient_dept.wait_times) > 0:
              self.wait_times_inpatient.append(sum(self.inpatient_dept.wait_times) / len(self.inpatient_dept.wait_times))
          if len(self.outpatient_dept.wait_times) > 0:
              self.wait_times_outpatient.append(sum(self.outpatient_dept.wait_times) / len(self.outpatient_dept.wait_times))
          self.utilization_emergency += self.emergency_dept.beds.count / SIM_TIME
          self.utilization_inpatient += self.inpatient_dept.beds.count / SIM_TIME
          self.utilization_outpatient += self.outpatient_dept.exam_rooms.count / SIM_TIME
          yield self.env.timeout(1)   # collect statistics every 1 time unit



    def run_simulation(self):
      self.env.process(self.generate_patients())
      self.env.process(self.collect_statistics())
      self.env.run(until=SIM_TIME)

      if self.wait_times_emergency:
          print(f"Average wait time for emergency patients: {self.wait_times_emergency[-1]}")
      else:
          print("No emergency patients during simulation")

      if self.wait_times_inpatient:
        print(f"Average wait time for inpatient patients: {self.wait_times_inpatient[-1]}")
      else:
        print("No inpatient patients during simulation")

      if self.wait_times_outpatient:      
        print(f"Average wait time for outpatient patients: {self.wait_times_outpatient[-1]}")
      else:
          print("No outpatient patients during simulation")  
      print(f"Utilization rate for emergency department: {self.utilization_emergency/SIM_TIME*100}%")
      print(f"Utilization rate for inpatient department: {self.utilization_inpatient/SIM_TIME*100}%")
      print(f"Utilization rate for outpatient department: {self.utilization_outpatient/SIM_TIME*100}%")

                
env = simpy.Environment()
hospital = Hospital(env)
hospital.run_simulation()
