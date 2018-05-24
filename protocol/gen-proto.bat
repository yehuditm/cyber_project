rem gen python proto
protoc -I=. --python_out=../client data.proto
protoc -I=. --python_out=../server data.proto

rem gen cpp proto
rem protoc -I=../ --cpp_out=../../client ../data.proto
rem protoc -I=../ --cpp_out=../../server ../data.proto
