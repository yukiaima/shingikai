@echo on
setlocal
rem python�\�[�X�R�[�h�̃f�B���N�g���ֈړ�
cd src

rem python�R�[�h�����s ���I��������͍̂X�V���Ȃ�
python 100_���������s�ꌟ�����ψ���.py
python 101_�����͂̍ו����y�эL�撲�B�̋Z�p�I�����Ɋւ����Ɖ�.py
python 102_�����͋y�ю����o�����X�]�����Ɋւ���ψ���.py
python 103_�L��n�������ψ���.py
python 104_�L��A�n�n���̃}�X�^�[�v�����y�ьn�����p���[���݂̍�����Ɋւ��錟���ψ���.py
python 105_�e�ʎs��݂̍�����Ɋւ��錟����E�׋���.py
python 106_�n��ԘA�n���y�ђn�����d�n���̗��p���[�����Ɋւ��錟����.py
python 107_�O���b�h�R�[�h������.py
rem python 108_�d�̓��W���G���X���Ɋւ��鏬�ψ���.py
rem python 109_�n���n���̍��G�Ǘ��Ɋւ���׋���.py
python 110_�^�p�e�ʌ�����.py
python 111_�}�[�W��������.py
python 112_�����̓d�͎����V�i���I�Ɋւ��錟����.py
python 113_�����̉^�p�e�ʓ��݂̍���Ɋւ����Ɖ�.py
python 200_�d�́E�K�X��{���􏬈ψ���.py
python 201_���x������ƕ���.py
python 202_�K�X���Ɛ��x�������[�L���O�O���[�v.py
python 203_�Đ��\�G�l���M�[��ʓ����E������d�̓l�b�g���[�N���ψ���.py
rem python 204_�����\�ȓd�̓V�X�e���\�z���ψ���.py
python 205_�n�����[�L���O�O���[�v.py
rem python 206_����ׂ����d�͎s��A���������s��y�ю����^�p�̎����Ɍ���������������ƕ���.py
rem python 207_���d�͎s��A���������s��y�ю����^�p�݂̍���׋���.py
python 208_�Ζ��E�V�R�K�X���ψ���.py
python 209_���f���􏬈ψ���.py
python 210_�A�����j�A���E�Y�f�R�����􏬈ψ���.py
python 211_�d�͍L��I�^�c���i�@�֌��؃��[�L���O�O���[�v.py 
python 212_������̕��U�^�d�̓V�X�e���Ɋւ��錟����.py 
rem python 213_�����̓d�͎����Ɋւ���݂���׋���.py
python 214_�����s��݂̍�����Ɋւ��錟����.py
rem python 300_���x�݌v���.py
python 301_�������x���.py
rem python 302_�d�C�����R�����.py
rem python 303_�������x���[�L���O�E�O���[�v.py
python 304_���z�d�������E�v��i���m�F���[�L���O�O���[�v.py
rem python 305_���z�d�Ԃ̈ێ��E�^�p��p�̕��S�݂̍���������[�L���O�E�O���[�v.py
rem python 306_�ǒn�I�d�͎��v�����Ƒ��z�d�l�b�g���[�N�Ɋւ��錤����.py
python 307_���x�݌v�E�Ď����.py
python 900_���m�l�ނ̎Y�ƊE�ւ̓��E�o�H�̑��l���Ɋւ���׋���.py

rem ���̃f�B���N�g���ֈړ�
cd ..

rem github��push
git add . && ^
git commit -m "%DATE% %TIME% update" && ^
git push -u origin main  

exit /b 0
