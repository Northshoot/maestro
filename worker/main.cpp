#include<iostream>
#include<stdio.h>
#include<unistd.h>

int main()
{
	int counter = 0;
	while(counter < 5)
	{
		std::cout << "Hello !!!\n";
		sleep(1);
	counter++;
	}
} 
