# Python Laptime Measurement System

 **Python�x�[�X�̃��b�v�^�C���v���V�X�e��**

�E�F�u�J�������g�p���ă��A���^�C���Ń��[�X�J�[�̃��b�v�^�C�����v���\������V�X�e���ł��B

##  ��ȋ@�\

- **���A���^�C�����̌��o**: OpenCV�ɂ��ԗ����o�ǐ�
- **���b�v�^�C���v��**: �����x�ȃ^�C���v��
- **�`�[���Ǘ�**: �����`�[���̐��ъǗ�
- **GUI�\��**: Pygame�ɂ�钼���I�ȃC���^�[�t�F�[�X
- **�f�[�^�ۑ�**: JSON�`���ł̌��ʕۑ�
- **��������**: ���b�v�������̉����t�B�[�h�o�b�N

##  �V�X�e���v��

### �n�[�h�E�F�A
- **�E�F�u�J����**: USB�ڑ��܂��̓l�b�g���[�N�J����
- **PC**: Windows/macOS/Linux�Ή�
- **�����o��**: �X�s�[�J�[�܂��̓w�b�h�t�H��

### �\�t�g�E�F�A
- **Python**: 3.8�ȏ�
- **OpenCV**: 4.5�ȏ�
- **Pygame**: 2.0�ȏ�
- **NumPy**: 1.20�ȏ�

##  �C���X�g�[��

`ash
# ���|�W�g�����N���[��
git clone https://github.com/nkoba3292/python-laptime-measurement.git
cd python-laptime-measurement

# �K�v�ˑ��֌W���C���X�g�[��
pip install -r requirements.txt
`

##  �g�p���@

### ��{�I�Ȏg�p
`ash
python main_laptime_system.py
`

### �ݒ�t�@�C��
config.json�ŃV�X�e���p�����[�^�𒲐��\

##  ������@

### �L�[�{�[�h����
- **S**: ���[�X�J�n
- **R**: �V�X�e�����Z�b�g
- **Q/ESC**: �V�X�e���I��
- **SPACE**: �ꎞ��~/�ĊJ

### �}�E�X����
- **�N���b�N**: ���o�G���A�ݒ�
- **�h���b�O**: �G���A�͈͒���

##  �@�\�ڍ�

### 1. ���̌��o�V�X�e��
- **�w�i�����@**: ���I�w�i�X�V
- **�ԗ����o**: �֊s���o�ǐ�
- **�m�C�Y�t�B���^**: �댟�o����

### 2. ���b�v�^�C���v��
- **�����x�v��**: �~���b�P�ʂł̌v��
- **�������b�v�Ή�**: �ő�3���܂Ōv��
- **�x�X�g�^�C���L�^**: �����x�X�g�^�C���X�V

### 3. �`�[���Ǘ�
- **���ъǗ�**: �`�[���ʋL�^�ێ�
- **�����L���O�\��**: ���A���^�C�����ʕ\��
- **���ʕۑ�**: JSON�`���ł̃f�[�^�~�ϕێ�

##  �v���W�F�N�g�\��

`
python-laptime-measurement/
 main_laptime_system.py     # ���C���v���O����
 config.json                # �ݒ�t�@�C��
 requirements.txt           # �K�v�ˑ��֌W
 README.md                  # ���̃t�@�C��
 LICENSE                    # ���C�Z���X
 data/                      # ���ʃf�[�^
    race_result_*.json
 sounds/                    # �����t�@�C��
    start.wav
    finish.wav
 .vscode/                   # VS Code�ݒ�
     extensions.json
     settings.json
`

##  �J���J�X�^�}�C�Y

### ���o�p�����[�^����
- motion_pixels_threshold: ���쌟�o�̊��x
- min_contour_area: �ŏ����o�T�C�Y
- detection_cooldown: �A�����o�h�~����

### �J�����ݒ�
- camera_overview_id: �S�̕\���p�J����
- camera_start_line_id: �X�^�[�g���C���p�J����

##  ���H�p�r

- **�~�j�l�샌�[�X**: �����`�[�������v��
- **���W�R�����[�X**: �������̑Ή�
- **���ԃ��[�X**: ��^���̌��o
- **�w�Z���Z**: �l�����o�]�p

##  �g���u���V���[�e�B���O

### �J�������F������Ȃ�
`ash
# �J�����f�o�C�X�m�F
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).read()[0]])"
`

### ���o���x���Ⴂ
1. �Ɩ����������P
2. motion_pixels_threshold�𒲐�
3. �J�����ʒu�p�x��ύX

### �������o�͂���Ȃ�
- Pygame�̉����h���C�o�m�F
- �V�X�e�����ʐݒ�m�F
- �����t�@�C���`���m�F

##  �X�V����

### v13 (�ŐV)
- ���o�A���S���Y�����P
- GUI�\���œK��
- ���萫����

##  �R���g���r���[�V����

1. Fork���ău�����`�쐬
2. �@�\�ǉ��o�O�C��
3. �e�X�g���s
4. Pull Request�쐬

##  ���C�Z���X

MIT License - �ڍׂ�[LICENSE](LICENSE)�t�@�C�����Q��

##  �쐬��

- **nkoba3292**
- GitHub: [@nkoba3292](https://github.com/nkoba3292)

##  �֘A�v���W�F�N�g

- [ESP32S3SENSE-Security-Webcamera](https://github.com/nkoba3292/ESP32S3SENSE-Security-Webcamera) - ESP32�x�[�X�Z�L�����e�B�J����
