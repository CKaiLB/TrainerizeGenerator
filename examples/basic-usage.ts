import { createFitnessProgramGenerator, defaultConfig } from '../src/main';

async function main() {
  console.log('🚀 Starting Fitness Program Generator Example...\n');

  // Initialize the generator with default configuration
  const generator = createFitnessProgramGenerator(defaultConfig);

  // Example survey input
  const surveyInput = {
    name: "Sarah Johnson",
    email: "sarah.johnson@example.com",
    age: 28,
    weight: 65, // kg
    height: 165, // cm
    experienceLevel: "intermediate",
    primaryGoal: "hypertrophy",
    secondaryGoal: "strength",
    availableEquipment: ["dumbbells", "barbell", "bench", "squat-rack"],
    workoutFrequency: 4,
    sessionDuration: 75,
    preferredWorkoutDays: ["monday", "wednesday", "friday", "saturday"],
    injuries: [
      {
        bodyPart: "lower-back",
        severity: "mild",
        description: "Occasional tightness",
        recoveryStatus: "recovered",
        restrictions: []
      }
    ],
    medicalConditions: [],
    mobilityIssues: ["tight-hip-flexors"],
    preferredExerciseTypes: ["compound", "isolation"],
    dislikedExercises: ["burpees", "mountain-climbers"],
    timeOfDay: "evening",
    programDuration: 16,
    deloadFrequency: 4,
    progressionStyle: "linear"
  };

  console.log('📋 Survey Input:');
  console.log(JSON.stringify(surveyInput, null, 2));
  console.log('\n' + '='.repeat(50) + '\n');

  try {
    // Generate the fitness program
    console.log('🤖 Generating fitness program...');
    const startTime = Date.now();
    
    const result = await generator.generateProgram({ surveyInput });
    
    const generationTime = Date.now() - startTime;
    console.log(`⏱️  Generation completed in ${generationTime}ms\n`);

    if (result.success) {
      console.log('✅ Program generated successfully!');
      console.log(`📊 Program ID: ${result.programId}`);
      console.log(`🔗 Trainerize Program ID: ${result.trainerizeProgramId}`);
      console.log(`👤 Client ID: ${result.clientId}`);
      console.log(`📈 Metadata:`);
      console.log(`   - Total Workouts: ${result.metadata.totalWorkouts}`);
      console.log(`   - Total Weeks: ${result.metadata.totalWeeks}`);
      console.log(`   - Estimated Duration: ${result.metadata.estimatedDuration} minutes`);
      
      if (result.warnings.length > 0) {
        console.log(`⚠️  Warnings:`);
        result.warnings.forEach(warning => console.log(`   - ${warning}`));
      }

      // Get the generated program details
      const program = await generator.getProgram(result.programId!);
      if (program) {
        console.log('\n📋 Program Details:');
        console.log(`   - Client: ${program.clientProfile.name}`);
        console.log(`   - Goal: ${program.clientProfile.primaryGoal}`);
        console.log(`   - Experience: ${program.clientProfile.experienceLevel}`);
        console.log(`   - Equipment: ${program.clientProfile.availableEquipment.join(', ')}`);
        
        console.log('\n🏋️  Program Structure:');
        program.fitnessProgram.blocks.forEach((block, index) => {
          console.log(`   Block ${index + 1} (Weeks ${block.startWeek}-${block.endWeek}):`);
          console.log(`     - Focus: ${block.primaryFocus.type} (${block.primaryFocus.intensity} intensity)`);
          console.log(`     - Workouts: ${block.workouts.length}`);
          if (block.deloadWeek) {
            console.log(`     - Deload Week`);
          }
        });

        // Show first workout as example
        const firstBlock = program.fitnessProgram.blocks[0];
        const firstWorkout = firstBlock.workouts[0];
        
        console.log('\n💪 Example Workout (First Workout):');
        console.log(`   Name: ${firstWorkout.name}`);
        console.log(`   Duration: ${firstWorkout.estimatedDuration} minutes`);
        console.log(`   Target Days: ${firstWorkout.targetDays.join(', ')}`);
        console.log(`   Exercises: ${firstWorkout.exercises.length}`);
        
        firstWorkout.exercises.forEach((exercise, index) => {
          console.log(`     ${index + 1}. ${exercise.name}`);
          console.log(`        - Category: ${exercise.category}`);
          console.log(`        - Muscle Groups: ${exercise.muscleGroups.join(', ')}`);
          console.log(`        - Sets: ${exercise.sets.length}`);
          console.log(`        - Difficulty: ${exercise.difficulty}`);
        });
      }

      // Get client progress
      const progress = await generator.getClientProgress(result.clientId!);
      if (progress) {
        console.log('\n📊 Client Progress:');
        console.log(`   - Current Week: ${progress.currentWeek}`);
        console.log(`   - Completed Workouts: ${progress.completedWorkouts}/${progress.totalWorkouts}`);
        console.log(`   - Progress: ${progress.progressPercentage.toFixed(1)}%`);
        console.log(`   - Adherence Rate: ${progress.adherenceRate.toFixed(1)}%`);
      }

      // Get system health
      const health = await generator.getSystemHealth();
      console.log('\n🏥 System Health:');
      console.log(`   - Status: ${health.status}`);
      console.log(`   - Total Programs: ${health.metrics.totalPrograms}`);
      console.log(`   - Total Clients: ${health.metrics.totalClients}`);
      console.log(`   - Average Progress: ${health.metrics.averageProgress.toFixed(1)}%`);

    } else {
      console.log('❌ Program generation failed!');
      console.log('Errors:');
      result.errors.forEach(error => console.log(`   - ${error}`));
    }

  } catch (error) {
    console.error('💥 Unexpected error:', error);
  }

  console.log('\n' + '='.repeat(50));
  console.log('🎉 Example completed!');
}

// Run the example
main().catch(console.error); 