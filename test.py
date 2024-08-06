import holoocean
import numpy as np
import datetime
import sys,os
import pandas as pd
import traceback

realdata = (pd.read_excel("./realstate1.xlsx", usecols = "A,C,E,F,H,T,U")).values
realtime = realdata[:,0].tolist()
realdep = realdata[:,1].tolist()
realstern = realdata[:,2].tolist()
realyaw = realdata[:,3].tolist()
realrudder = realdata[:,4].tolist()
realroll = realdata[:,5].tolist()
realpitch = realdata[:,-1].tolist()

mkfile_time = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M%S')
fpath=f"./data/{mkfile_time}"
if not os.path.exists(fpath):
   os.makedirs(fpath)

def savexlsx(j):
   data_name_list = [  'time','Depth',
                       'wx_v','wy_v','wz_v',
                       'Acc_X','Acc_Y','Acc_Z',#單位 m/s^2
                       'Ang_X','Ang_Y','Ang_Z',#單位 rad/s
                       'x','y','z',# 單位 m
                       'roll','pitch','yaw', #單位 degrees
                       'hrudder','vrudder','thrust']
   compare_data_list = ['realtime',
                        'real_Depth','depth',
                        'real_roll','roll',
                        'real_pitch','pitch',
                        'real_yaw','yaw']
   df = pd.DataFrame(StateVec,columns = data_name_list)
   df1 = pd.DataFrame(compare_data,columns = compare_data_list)
   with pd.ExcelWriter(f"{fpath}/state{j}.xlsx") as writer:

      df.to_excel(writer,sheet_name="Simulate_State",index=True)
      df1.to_excel(writer,sheet_name="Compare",index=True)
   print('Done!')

def everyhalfsecond(command):
   for _ in range(100):
      state = env.step(command)
   return state

# The Torpedo AUV takes a command for each thruster
stable_time = 10
MAX_STEPS =  45 # 總秒數(s)

stern_ang = 0 # 正下潛 負上浮
rudder_ang = 0 # 正AUV向右 負AUV向左
auv_push = 0 # 
max_push = 550 # rpm
sway_force = 0
stern_ratio = 1.5
try:
   env = holoocean.make("SimpleUnderwater-Custom",show_viewport=True) 
   for j in range(1):
      if j!=0:env.reset()
      StateVec = [np.zeros(20)]
      compare_data = []
      prev_depth = 0
      for step in range((MAX_STEPS + stable_time)*2):
         if step < stable_time*2:
            command = np.array([0,0,0,0,0,sway_force,stern_ratio,stern_ratio])
            state = everyhalfsecond(command)  
         else:
            i = step-stable_time*2
            stern_ang = round(realstern[i])
            rudder_ang = -round(realrudder[i])*0
            if auv_push<=max_push:
               auv_push+=200
               if auv_push>max_push: auv_push = max_push
            command = np.array([stern_ang,rudder_ang,-stern_ang,-rudder_ang,auv_push,sway_force,stern_ratio,stern_ratio]) # [left_fin, top_fin, right_fin, bottom_fin, thrust] fin range -30~30 ,thrust range -100~100(100=4m/s)

            state = everyhalfsecond(command)

            depth = np.array(state.get('DepthSensor',prev_depth)).tolist()

            prev_depth = depth # z position (m)


            stepdata = [state['t']-stable_time,
                        depth,
                        state['VelocitySensor'].tolist(),
                        state['IMUSensor'][0].tolist(),
                        state['IMUSensor'][1].tolist(),
                        state['LocationSensor'].tolist(),
                        state['RotationSensor'].tolist(),
                        stern_ang,
                        rudder_ang,
                        auv_push]
            compare_state = [realtime[i],
                           realdep[i],depth,
                           realroll[i],state['RotationSensor'][0],
                           realpitch[i],-state['RotationSensor'][1],
                           realyaw[i],180-state['RotationSensor'][2]
                           ]

            StateVec.append(np.hstack(stepdata))
            compare_data.append(np.hstack(compare_state))
      savexlsx(j)
except Exception as e:
   #savexlsx(j)
   print(e)
   traceback.print_exc()