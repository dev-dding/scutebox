# Makefile for building broadcast server

source_dir=$(CURDIR)/
obj_dir=$(CURDIR)/obj/
build_dir=$(CURDIR)/build/
MKDIR_P=mkdir -p
CC=gcc
CFLAGS=-c -Wall

all: directories bserver dist

directories:
	${MKDIR_P} ${build_dir}

bserver: bserver.o
	$(CC) bserver.o -o bserver

bserver.o: bserver.c
	$(CC) $(CFLAGS) bserver.c

clean:
	rm -rf $(build_dir)

dist: 
	mv -f ./bserver $(build_dir)
	rm -f ./bserver.o
	cp -f ./install.sh $(build_dir)
	chmod +x $(build_dir)install.sh
	cp -f ./scute.cron $(build_dir)
	cp -f ./updateip.py $(build_dir)
	cp -f ./bserver.service $(build_dir)
