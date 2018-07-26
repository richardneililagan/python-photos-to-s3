import os
import cv2
import boto3
import uuid
import time
from time import strftime, localtime

# :: mimic device ID
device_id = uuid.uuid4().hex

# :: subprocesses
upload_tasks = []

# :: AWS
bucketname = os.environ.get('BUCKET_NAME', 'test-bucket')
s3_client = boto3.client('s3')

# :: Camera
cam = cv2.VideoCapture(0)
poll_interval = int(os.environ.get('CAPTURE_INTERVAL', 15))

# :: ---

timestamp = int(time.time())

while True:
  newtime = int(time.time())
  delta = newtime - timestamp

  if delta < poll_interval:
    continue

  # :: take picture
  ret, frame = cam.read()
  filename = strftime("%Y%m%d%H%M%S", localtime()) + '_' + device_id + '.png'

  cv2.imwrite(filename, frame)
  print (">> file written " + filename)

  # :: upload the file to S3
  task = os.fork()
  if (task == 0):
    s3_client.upload_file(filename, bucketname, filename)
    print ('>> file %s uploaded to S3' % filename)
    os.remove(filename)
    os._exit(0)
  else:
    print ('>> child forked, pid = %d' % task)
    upload_tasks.append(task)

  timestamp = newtime

  # :: manage tasks
  for upload_task in upload_tasks:
    pid, sts = os.waitpid(upload_task, os.WNOHANG)
    if (pid == upload_task):
      upload_tasks.remove(upload_task)

  if cv2.waitKey(1) & 0xFF == ord('q'):
    break

cam.release()
cv2.destroyAllWindows()