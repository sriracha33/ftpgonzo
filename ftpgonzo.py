import os
import sys
import glob
import time
import base64
import socket
import ftplib
import fnmatch
import zipfile
import Tkinter as tk
import ttk
from multiprocessing import Process, Queue
import multiprocessing
from threading import Thread
from tkMessageBox import askquestion, askyesno
from tkFileDialog import askopenfilename, askdirectory


#temporary.  We'll add it to the non class function calls later
blocksize=1024


class MainApplication:
	def __init__(self,parent):
		
		#class variables
		self.host=tk.StringVar(value='192.168.2.19')
		self.blocksize=1024
		
		
		#initialize 
		self.parent=parent
		self.parent.title("FTP Gonzo")
		self.parent.geometry("800x400+300+300")
		self.parent.resizable(True,True)
		self.parent.minsize(800,400)
		
		try:       
			base_path = sys._MEIPASS
		except Exception:
			base_path = os.path.abspath(".")
		iconfile=os.path.join(base_path, "gonzo.ico")
		self.parent.iconbitmap(default=iconfile)
		
		#Set up Menus#
		menubar = tk.Menu(root)
		root.config(menu=menubar)
		
		#file menu
		filemenu = tk.Menu(menubar, tearoff=0)
		filemenu.add_command(label="Create Disk From Template", command=self.file_template)
		filemenu.add_separator()
		filemenu.add_command(label="Exit", command=self.parent.destroy)
		menubar.add_cascade(label="File", menu=filemenu)		
		
		#help menu
		helpmenu = tk.Menu(menubar, tearoff=0)
		helpmenu.add_command(label="About", command=self.help_about)
		menubar.add_cascade(label="Help", menu=helpmenu)
		
		#split window into two panes
		paned=tk.PanedWindow(parent,orient='horizontal')
		paned.pack(fill='both',expand=1)		
		
		#add frame to each pane.
		command_frame=tk.Frame(paned)
		paned.add(command_frame, minsize=250, padx=2)
		command_frame.pack_propagate(0)
		status_frame=tk.Frame(paned, background="green")
		paned.add(status_frame, minsize=350, padx=2)	
		
		#left Pane#
		
		#add buttons at bottom 
		clear_button=tk.Button(command_frame, text="Clear All Disks", command=self.clear_disks,state='disabled')#, relief="ridge"
		clear_button.pack(side="bottom", fill="x", padx=1,pady=2)		
		delete_button=tk.Button(command_frame, text="Delete Disk/Command", command=self.delete_disk,state='disabled')#, relief="ridge"
		delete_button.pack(side="bottom", fill="x", padx=1,pady=(0,2))
		add_button=tk.Button(command_frame, text="Add Disk", command=self.add_disk,state='active')#, relief="ridge"
		add_button.pack(side="bottom", fill="x", padx=1,pady=2)
		
		#report type selection box
		command_lframe=tk.LabelFrame(command_frame,text="Command Files")
		command_lframe.pack(side='bottom', fill='both', expand=True)		
		command_vscroll = tk.Scrollbar(command_lframe)
		command_vscroll.pack(side='right', fill='y', padx=(0,2), pady=(0,2))			
		disk_tree=ttk.Treeview(command_lframe, show='tree', selectmode='browse')
		command_lframe.pack(side='bottom', fill='both')		
		disk_tree.column("#0",stretch=True)
		#disk_tree.column("#0", width = 120, stretch=0)
		disk_tree.pack(side='bottom',fill='both',anchor='s', padx=(2,0), pady=(0,2), expand=True)
		command_vscroll.config(command=disk_tree.yview)
		disk_tree.configure(yscrollcommand=command_vscroll.set)	
		disk_tree.bind("<<TreeviewSelect>>",self.set_delete_state)
		
		# Right Pane
		
		ip_frame=tk.Frame(status_frame)
		ip_frame.pack(side='top',anchor='n', expand=False, fill='x') 
		tk.Label(ip_frame, text="Target IP Address: ").pack(side='left', anchor='w')
		host_entry=tk.Entry(ip_frame, textvariable=self.host, width=15)
		host_entry.pack(side='left', anchor='w')
		execute_button=tk.Button(ip_frame, text='Execute Commands', command=self.execute_commands, padx=2, state='disabled')
		execute_button.pack(side='right', anchor='e')
		
		history_lframe=tk.LabelFrame(status_frame,text="History", padx=5, pady=5)
		history_lframe.pack(side='top', fill='both', expand=True)		
		history_vscroll = tk.Scrollbar(history_lframe)
		history_vscroll.pack(side='right', fill='y', padx=(0,2), pady=(0,2))		
		history_hscroll = tk.Scrollbar(history_lframe, orient='horizontal')
		history_hscroll.pack(side='bottom', fill='x', padx=(0,2), pady=(0,2))	
		history_text=tk.Text(history_lframe, wrap='none', state='disabled')
		history_text.pack(side='bottom', fill='both', expand=True)			
		
		history_vscroll.config(command=history_text.yview)
		history_text.configure(yscrollcommand=history_vscroll.set)			
		history_hscroll.config(command=history_text.xview)
		history_text.configure(xscrollcommand=history_hscroll.set)		
		
		#class variables
		self.disk_tree=disk_tree
		self.history_text=history_text
		self.add_button=add_button
		self.delete_button=delete_button
		self.clear_button=clear_button
		self.execute_button=execute_button
		
		

	def file_template(self):
		
		#selects the right base path depending on if it's run as a .py script or packaged as an exe
		try:
			# PyInstaller creates a temp folder and stores path in _MEIPASS
			base_path = sys._MEIPASS
		except Exception:
			base_path = os.path.abspath(".")		
		
		selecttemplate = askopenfilename(title='Select Disk Template',filetypes=[('Zip File','*.zip'),("All Files", "*.*"),],defaultextension = '.zip', initialdir=base_path+"/templates")
		
		if not selecttemplate:
			return
		
		selectsave = askdirectory(title='Select Location to Save Disk')
		
		if not selectsave:
			return		
		
		if len(os.listdir(selectsave))!=0:
			answer = askyesno("Overwrite Directory?","Directory is not empty.  Would you still like to extract template to this directory?")
			if not answer:
				return
		
		with zipfile.ZipFile(selecttemplate, 'r') as zip_ref:
			zip_ref.extractall(selectsave)		
		
		answer = askyesno("Load Command File?","Would you like to load a command file from the new disk?")
		if not answer:
			return		
		self.add_disk(selectsave)
		
	def help_about(self):
		"""Function to load the About window from the Help menu"""
		if hasattr(self, 'about_win') and self.about_win.winfo_exists():
			self.about_win.deiconify()
			self.about_win.focus_force()
			self.about_win.lift()
			return
		
		#create window and set size/location
		self.about_win = tk.Toplevel()
		x = self.parent.winfo_rootx()
		y = self.parent.winfo_rooty()
		
		self.about_win.geometry("200x75+%d+%d" % (x+150,y+100))
		self.about_win.resizable(False,False)		
		self.about_win.title("About")
		self.about_win.tk.call('wm', 'iconphoto', self.about_win._w, self.icon)
		tk.Label(self.about_win, text="FTP Gonzo\nWritten by Andrew Webber\nVersion 1.1\nApril 15, 2022", anchor='w', justify='left').pack(side='top', fill='x')	
		
	
	def add_disk(self,path=os.getcwd()):
		selectfilename = askopenfilename(title='Select Gonzo File',filetypes=[('Gonzo File','*.sav *.put'),("All Files", "*.*"),],initialdir=path)
		
		if not selectfilename:
			return
		
		#open new gonzo file
		gonzofile=open(selectfilename,'rb')
		#gonzopath=os.path.dirname(gonzofile.name)
		filedata=gonzofile.readlines()
		gonzofile.close()
		
		#if there are commands, add them to the tree.  If not, do nothing
		if filedata:
			iid=self.disk_tree.insert('', tk.END, text=selectfilename, open=False)	
			
			history_line = "Added: %s\n" % gonzofile.name
			self.print_text(self.history_text,history_line)
					
			#process each line of the gonzo file
			for line in filedata:		
				self.disk_tree.insert(iid,'end',text=line.strip())
		else:
			self.print_text(self.history_text,'No Commands Found for %s\n' % gonzofile.name)
			
		#check if there are any disks/commands.  If so, execute button enabled, if not then disable it.  Clear will always be the same!
		if self.disk_tree.get_children():
			self.execute_button.configure(state='active')
			self.clear_button.configure(state='active')
		else:
			self.execute_button.configure(state='disabled')		
			self.clear_button.configure(state='disabled')		
		
			
				
	def delete_disk(self):
		#get what item is selected
		selected_disk = self.disk_tree.focus()
		
		#this shouldn't happen, best to be careful
		if selected_disk is '':
			self.execute_button.configure(state='disabled')
			return
		
		#check if item was a child of a disk (a command).
		parent=self.disk_tree.parent(selected_disk)
		
		#delete the item
		self.disk_tree.delete(selected_disk)
		
		#if item was a child of a disk, check if any other children (commands) remain.  If not, delete parent as well.
		if parent is not '' and not self.disk_tree.get_children(parent):
			self.disk_tree.delete(parent)
			
		#check focus. there should be no focus so it should always disable button, but best to be careful
		selected_disk = self.disk_tree.focus()
		if selected_disk:
			self.delete_button.configure(state='active')
		else:
			self.delete_button.configure(state='disabled')	
		
		#check if there are any disks/commands.  If so, execute button enabled, if not then disable it. Clear will always be the same!
		if self.disk_tree.get_children():
			self.execute_button.configure(state='active')
			self.clear_button.configure(state='active')
		else:
			self.execute_button.configure(state='disabled')
			self.clear_button.configure(state='disabled')
	
	#method to clear all disks
	def clear_disks(self):
		for item in self.disk_tree.get_children():
			self.disk_tree.delete(item)		
		
		#check if there are any disks/commands.  If so, execute button enabled, if not then disable it. Clear will always be the same!
		if self.disk_tree.get_children():
			self.execute_button.configure(state='active')
			self.clear_button.configure(state='active')
		else:
			self.execute_button.configure(state='disabled')
			self.clear_button.configure(state='disabled')		
	
	#method to run ftp/gonzo commands
	def execute_commands(self):
		#set buttons states and selections
		for item in self.disk_tree.selection():
			self.disk_tree.selection_remove(item)		
		self.set_button_states(True)
		
		#get list of disks by iid
		diskIDs=self.disk_tree.get_children()	
		
		#this shouldn't be needed, but just in case...
		if not diskIDs:
			self.print_text(self.history_text,'No gonzo files loaded.  Aborting.')
			#put buttons back to normal		
			self.set_button_states(False)				
			return		
		
		disks=[]
		#compile disks into lists of disks and commands
		for diskID in diskIDs:
			disks.append({'name':self.disk_tree.item(diskID)['text'] , 'commands':[]})
			commandIDs = self.disk_tree.get_children(diskID)
			for commandID in commandIDs:
				line=self.disk_tree.item(commandID)['text']
				disks[-1]['commands'].append(line)
				
		#print disks
		#clear out the history window
		self.print_text(self.history_text,'',True)			
		
		#Queue variable to capture output
		self.queue=Queue()
		
		#begin processing transfers via thread
		self.thread=Process(target=execute_transfers, args=((self.host.get(),disks,self.queue)))
		self.thread.start()
		self.parent.after(100, lambda: self.monitor_thread())
		
	
	
	#method to monitor current thread for ftp login
	def monitor_thread(self):
		while not self.queue.empty():
			#error check to make sure it's a string
			self.print_text(self.history_text,self.queue.get())
		if self.thread.is_alive():
			# check the thread every 100ms
			self.parent.after(100, lambda: self.monitor_thread())
		else:
			self.thread.join()
			self.set_button_states(False)		
	
	#method to print text to a desired text box.  clear is an option argument to clear the box first
	def print_text(self,textbox,text,clear=False):
		self.history_text.configure(state='normal')
		if clear:
			textbox.delete("1.0","end")
		self.history_text.insert('end',text)							
		self.history_text.configure(state='disabled')
		self.history_text.yview('end')
		print text,
			
	
	
	
	#method to set state of delete button (to active) when an item is selected
	def set_delete_state(self,event):
		widget=event.widget
		if widget:
			self.delete_button.configure(state='active')
		else:
			self.delete_button.configure(state='disabled')
	
	#method to set states based on if program is running or not.
	def set_button_states(self, running):
		if running:
			self.execute_button.configure(state='disabled')
			self.delete_button.configure(state='disabled')
			self.add_button.configure(state='disabled')
			self.clear_button.configure(state='disabled')
			self.disk_tree.configure(selectmode='none')
		else:
			self.execute_button.configure(state='active')
			self.delete_button.configure(state='disabled')
			self.add_button.configure(state='active')			
			self.clear_button.configure(state='active')			
			self.disk_tree.configure(selectmode='browse')	


#non class functions

def execute_transfers(host,disks,queue):
		
	#set variables to be used for results
	errors=0
	transferred=0			
	
	#print 'Connecting to FTP server @ %s ...\n' % host
	queue.put('Connecting to FTP server @ %s ...\n' % host)
	
	try:
		ftp=ftplib.FTP(host, timeout=10)
		ftp.set_pasv(False)
		ftp.login()
		#print "Connected to FTP successfully\n"
		queue.put("Connected to FTP successfully\n\n")
	except:
		#print "Could Not Connect to IP Address: %s\n"% host
		queue.put("Could Not Connect to IP Address: %s\n\n"% host)
		return
		
	
	#process disks/commands
	for disk in disks:
		#get directory path of gonzo file so we know where to look for files or where to store files
		gonzopath=os.path.dirname(disk['name'])
		
		#print disk['name']
		queue.put(disk['name']+'\n')
		
		for command in disk['commands']:
			#process each line of the gonzo file
			line=command
			#get operation to see if this is a SEND or a RECV
			operation=line.strip().split(' ')[0]
			
			#print raw command
			#print line
			queue.put(line)
			
			#keep all slashes forward
			line=line.replace('\\','/')
			
			#perform SEND operation
			if operation.lower()=='s':
				(sendtransferred, senderrors) = ProcessSend(ftp,gonzopath,line,queue)
				transferred+=sendtransferred
				errors+=senderrors
			
			#perform RECV operation
			elif operation.lower()=='r':
				(recvtransferred, recverrors) = ProcessRecv(ftp,gonzopath,line,queue)
				transferred+=recvtransferred
				errors+=recverrors
					
			else:
				queue.put("\nUnknown Operation - Skipping")
			#print
			queue.put('\n\n')
	ftp.quit()
	queue.put("Transferred %d succesfully with %d errors.\n\n" % (transferred,errors))

def ProcessSend(ftp,gonzopath,line,queue):
	[operation,localTx,remoteTx]=line.strip().split()
	global blocksize
	transferred=0
	errors=0
	
	#add path to the localTx to use in glob function.  Needs full windows path.
	#if you're sending one file from the base there may be no leading /.  Need to add one if not
	if localTx[0]=='/':
		fulllocalTx=gonzopath+localTx
	else:
		fulllocalTx=gonzopath+'/'+localTx

	#get list of files.  If there's no * it should return one file.  If not it will return a list.  convert \ to / in the proocess.
	#filelist=glob.glob(fulllocalfile)
	filelist=[item.replace('\\','/').lower() for item in glob.glob(fulllocalTx)]

	#if no files are found, tell me about it.  Count it as an error? ntgonzo does (think ss01.sav).
	if filelist==[]:
		queue.put("\nNo files found for %s\n" % fulllocalTx)
		return (transferred,errors)

	#process each file found for this gonzo command.  Could many or one.  None gets kicked back earlier.
	for f in filelist:

		#glob returns directories too.  Don't process those.  In reality we don't need to output that it's skipped, left in for debugging for now.
		if os.path.isdir(f):
			queue.put("Skipping Subdirectory %s\n" % f)
			continue

		#if remote path ends in a / then filename is assumed from source path.  That means remoteTx is just the path.
		if remoteTx[-1]=='/':
			remotefilename=os.path.basename(f)
			remotepath=remoteTx
		#if it doesn't end with a /, the filename is specified.  It also means you need to take file name out of path.
		else:
			remotefilename=remoteTx.split('/')[-1]
			remotepath='/'.join(remoteTx.split('/')[0:-1])+"/"				

		#print operation being attemped
		queue.put('\n* SEND %s %s%s' % (f,remotepath,remotefilename))

		#if the directory remotepath cannot be reached, this whole command is bad.  Return.
		try:
			ftp.cwd(remotepath);
			pass
		except ftplib.error_perm:				
			queue.put("Command Failed - Remote Directory Not Found")
			errors+=1
			return (transferred,errors)

		#make sure file exists.  If not raise and error and move on
		if os.path.exists(f):
			pass
		else:
			queue.put("Skipped - Local File Not Found")
			error+=1
			continue
			
			
		#try to open the file and 
		try:
			ftpfile = open(f,'rb')
			#ftp.storbinary('STOR '+ remotefilename, ftpfile, blocksize, handleUpload)
			ftp.storbinary('STOR '+ remotefilename, ftpfile, blocksize,lambda block: handleUpload(block, queue))
			
			transferred+=1
			time.sleep(1)
			ftpfile.close() 
			queue.put(" OK")
		except IOError:
			queue.put(" Local File Open Failed")
			errors+=1
			continue
		except ftplib.all_errors:
			queue.put(" Upload Failed")
			ftpfile.close() 
			errors+=1
			continue
	return (transferred,errors)

def ProcessRecv(ftp,gonzopath,line,queue):
	[operation,remoteRx,localRx]=line.strip().split()
	global blocksize
	transferred=0
	errors=0	
	
	#get the name of the remote file/search, name of the path (for cwd in ftp), and where we're going to download to (may have filename, may not)
	remoteRxfile=remoteRx.split('/')[-1]
	remotepath='/'.join(remoteRx.split('/')[0:-1])+'/'
	fulllocalRx=gonzopath+localRx

	#check if you can get to the remote path.
	try:
		ftp.cwd(remotepath)
	except ftplib.error_perm:				
		print "Command Failed - Remote Directory Not Found"
		errors+=1
		return (transferred,errors)

	if '*' in remoteRxfile:
		#get the directory listing
		filelist=ftp.nlst()
		#put code here to filter entry list.  Remove directories an nonsense here. Then, if it's empty, report is as no files found.  Should this be an error?  Think ss01.sav
		filelist=filter(lambda x: len(x.split())==9 and x.split()[0][0].lower()!='d',filelist)
		if filelist==[]:
			#print "No files found for " + remoteRx
			queue.put("No files found for " + remoteRx + '\n')
			return (transferred,errors)
		
		#go through each file in the list and get it.
		for entry in filelist:
			filedetails=entry.split()				
			
			#get relevent info from file details
			remotefilepermissions=filedetails[0]
			remotefilename=filedetails[8]
			
			#if it's not a directory (so a file) and it matches the filesearch criteria, download the file
			if fnmatch.fnmatch(remotefilename,remoteRxfile):
				f=fulllocalRx+remotefilename
				#print " * RECV %s%s %s" % (remotepath,remotefilename,f),
				queue.put("\n * RECV %s%s %s" % (remotepath,remotefilename,f))
				
				#transfer the file
				try:
					ftpfile = open(f,'wb')
					ftp.retrbinary('RETR '+ remotefilename, lambda block: handleDownload(block, ftpfile, queue), blocksize)												
					transferred+=1
					time.sleep(.1) #?
					ftpfile.close() 
					#print "OK"					
					queue.put(" OK")
				except IOError:
					print " Local File Open Failed"
					errors+=1
					continue
				except ftplib.all_errors:
					print " Download Failed"
					ftpfile.close() 
					errors+=1
					continue
	#if the remote file name does not have a * in it, it's a specific file.  Get just that specific file
	else:
		#you can provide the name for the file or not.  if you do, it will call it that.  If not, it defaults to the nanme of the remote file.
		if fulllocalRx[-1]=='/':
			f=fulllocalRx+remoteRxfile
		else:
			f=fulllocalRx
		#print " * RECV %s%s %s" % (remotepath,remoteRxfile,f),
		queue.put("\n * RECV %s%s %s" % (remotepath,remoteRxfile,f))
		try:
			ftpfile = open(f,"wb")
			ftp.retrbinary('RETR ' + remoteRxfile, lambda block: handleDownload(block, ftpfile, queue), blocksize)
			transferred+=1
			time.sleep(.1)
			ftpfile.close()
			queue.put(' OK')
		except IOError:
			print "Local File Open Failed"
			errors+=1
		except ftplib.all_errors:
			print "Download Failed"
			ftpfile.close() 
			errors+=1
	return (transferred,errors)	
	
	
#functions to run during file transfers.
def handleDownload(block,fileToWrite,queue):
	fileToWrite.write(block)
	queue.put('.')

def handleUpload(block,queue):
	queue.put(",")

if __name__ == "__main__":
	try:
		multiprocessing.freeze_support() #needed
		root = tk.Tk()
		MainApplication(root)
		root.mainloop()
	except KeyboardInterrupt:
		pass