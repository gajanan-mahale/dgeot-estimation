import numpy as np

def get_factors(duty_cls):
    impact_map={"M1":1.06,"M2":1.12,"M3":1.18,"M4":1.25,"M5":1.32,"M6":1.4,"M7":1.5,"M8":1.5}
    duty_map={"M1":1.0,"M2":1.0,"M3":1.0,"M4":1.05,"M5":1.06,"M6":1.1,"M7":1.12,"M8":1.2}
    return impact_map.get(duty_cls.strip().upper(),1.32), duty_map.get(duty_cls.strip().upper(),1.06)

def get_box_girder(SWL_T, SPAN_M, W_CT_override=None, W_PLFM_override=None, duty="M5", IMPACT=None, DF=None, E=2.1e6):
    SPAN_M=float(SPAN_M); SWL_T=float(SWL_T); SWL=SWL_T*1000; SPAN=SPAN_M*100
    W_PLFM_default=65*SPAN_M+250
    W_PLFM=W_PLFM_override if W_PLFM_override is not None else W_PLFM_default
    WT_HOIST=0.2*SWL; P=(SWL+WT_HOIST)/2
    if IMPACT is None or DF is None:
        imp,df=get_factors(duty)
        if IMPACT is None: IMPACT=imp
        if DF is None: DF=df
    ALLOW_DEF_THEO=SPAN/750; ALLOW_DEF=ALLOW_DEF_THEO-0.025; BT_ALLOW=38
    if SWL_T<=10:
        t_top_list=[0.6,0.8,1.0,1.2,1.6,2.0,2.2,2.5,3.0]; t_bot_list=[0.6,0.8,1.0,1.2,1.6,2.0,2.2,2.5,3.0]; t_web_list=[0.6,0.8,1.0,1.2]
        h_start,h_end,h_step=60,140,2; b_add_max=6; B_INSIDE_BASE=round(SPAN/60)
    elif SWL_T<=25:
        t_top_list=[0.8,1.0,1.2,1.6,2.0,2.2,2.5,2.8,3.2]; t_bot_list=[0.8,1.0,1.2,1.6,2.0,2.2,2.5,2.8,3.2]; t_web_list=[0.8,1.0,1.2,1.6]
        h_start,h_end,h_step=80,140,5; b_add_max=8; B_INSIDE_BASE=round(SPAN/60)
    else:
        t_top_list=[1.0,1.2,1.6,2.0,2.5,3.2]; t_bot_list=[1.0,1.2,1.6,2.0,2.2,2.5,2.8,3.2]; t_web_list=[0.6,0.8,1.0,1.2,1.6,2.0]
        h_start,h_end,h_step=100,140,5; b_add_max=11; B_INSIDE_BASE=round(SPAN/50)
    if W_CT_override is not None: W_CT=W_CT_override
    else:
        if SWL_T<=5: W_CT=12.56*SPAN_M
        elif SWL_T<=15: W_CT=19.625*SPAN_M
        elif SWL_T<=30: W_CT=38.5*SPAN_M
        else: W_CT=52.0*SPAN_M
    def calc_section(t_top_in,b_inside_in,t_bot_in,t_web_in,h_web_in):
        t_top=t_top_in; t_bot=t_bot_in; t_web=t_web_in; h_web=h_web_in; b_inside=round(b_inside_in)
        if b_inside/t_top>BT_ALLOW: return None
        b_top=b_inside+5; b_bot=b_top; H=t_top+h_web+t_bot
        if SPAN/H>=25: return None
        A_top=b_top*t_top; A_bot=b_bot*t_bot; A_web=2*h_web*t_web; A=A_top+A_bot+A_web
        y_top=H-t_top/2; y_bot=t_bot/2; y_web=t_bot+h_web/2; Y_bar=(A_top*y_top+A_bot*y_bot+A_web*y_web)/A
        I_web_self=2*(t_web*h_web**3)/12; Ixx=(A_top*(y_top-Y_bar)**2+A_bot*(Y_bar-y_bot)**2+I_web_self); Ixx=abs(Ixx)
        Iyy_top=(t_top*b_top**3)/12; Iyy_bot=(t_bot*b_bot**3)/12; Iyy_web=2*(h_web*t_web)*(b_inside/2+t_web/2)**2; Iyy=Iyy_top+Iyy_bot+Iyy_web
        Z_top=Ixx/(H-Y_bar); Z_bot=Ixx/Y_bar; Z_yy=Iyy/(b_bot/2)
        W_plates=A*SPAN*0.00785*1.05; W_diaphragm=h_web*b_inside*0.6*0.007854*SPAN_M*1.9; Wg=1.03*(W_plates+W_diaphragm); W=Wg+W_CT+W_PLFM
        M=(P*SPAN/4)*IMPACT*DF+W*SPAN/8; delta_live=(P*SPAN**3)/(48*E*Ixx); delta_dead=(5*W*SPAN**3)/(384*E*Ixx)
        camber=abs(1.5*(delta_dead+delta_live*0.5)); camber=0.5 if camber<0.5 else round(camber*10)/10
        s_top=M/Z_top; s_bot=M/Z_bot; s_lat=(M*0.05)/Z_yy
        return {'b_top':b_top,'b_bot':b_bot,'b_inside':b_inside,'t_top':t_top,'t_bot':t_bot,'t_web':t_web,'h_web':h_web,'H':H,'W':W,'Wg':Wg,'W_CT':W_CT,'W_PLFM':W_PLFM,'M':M,'delta_live':delta_live,'Ixx':Ixx,'Iyy':Iyy,'s_top_comb':s_top+s_lat,'s_bot_comb':s_bot+s_lat,'ok_top_comb':(s_top+s_lat)<1200,'ok_bot_comb':(s_bot+s_lat)<1450,'ratio':SPAN/H,'ratio_ok':SPAN/H<25,'bt_ratio':b_inside/t_top,'bt_ok':b_inside/t_top<=38,'camber':camber,'ALLOW_DEF':ALLOW_DEF,'ALLOW_THEO':ALLOW_DEF_THEO,'B_BASE':B_INSIDE_BASE,'SWL_T':SWL_T,'SPAN_M':SPAN_M,'IMPACT':IMPACT,'DF':DF,'P':P,'SPAN':SPAN}
    solution=None; found_params=None
    for t_web in t_web_list:
        if solution: break
        for t_bot in t_bot_list:
            if solution: break
            allowed_t_top=[t for t in t_top_list if t < (2*t_bot-0.001)] if abs(t_bot-0.6)<0.001 else t_top_list
            for b_add in range(0,b_add_max):
                if solution: break
                b_inside=B_INSIDE_BASE+b_add
                for t_top in allowed_t_top:
                    if solution: break
                    for h_web in range(h_start,h_end,h_step):
                        r=calc_section(t_top,b_inside,t_bot,t_web,h_web)
                        if r is None: continue
                        if r['ok_top_comb'] and r['ok_bot_comb'] and r['ratio_ok'] and r['bt_ok'] and r['delta_live']<=ALLOW_DEF:
                            solution=r; found_params=(t_top,b_inside,t_bot,t_web,h_web); break
    if solution and found_params:
        t_top_curr,b_inside_curr,t_bot_curr,t_web_curr,h_web_curr=found_params
        try: idx_top=t_top_list.index(t_top_curr); next_t_top=t_top_list[idx_top+1] if idx_top+1<len(t_top_list) else t_top_curr
        except: next_t_top=t_top_curr
        try: idx_bot=t_bot_list.index(t_bot_curr); next_t_bot=t_bot_list[idx_bot+1] if idx_bot+1<len(t_bot_list) else t_bot_curr
        except: next_t_bot=t_bot_curr
        upgraded=calc_section(next_t_top,b_inside_curr,next_t_bot,t_web_curr,h_web_curr)
        if upgraded is not None:
            print(f"[UPGRADE] t_top {t_top_curr} -> {next_t_top} , t_bot {t_bot_curr} -> {next_t_bot} (next from set)")
            solution=upgraded
    return solution

# if __name__ == "__main__":

#     SWL_T = 10
#     SPAN_M = 25
#     duty = "M8"
#     W_CT_override = 0.2*SWL_T
#     IMPACT, DF = get_factors(duty)
#     W_PLFM_override = 65*SPAN_M + 250
#     E = 2.1E6
#     box_sol = get_box_girder(SWL_T, SPAN_M, W_CT_override, W_PLFM_override, duty, IMPACT, DF, E)
#     Wg=box_sol['Wg']
#     print(f"Box: H={box_sol['H']:.1f}cm Wg 1={Wg:.0f}Kg IMPACT={box_sol.get('IMPACT',IMPACT)} DF={box_sol.get('DF',DF)} Camber={box_sol['camber']}cm")

